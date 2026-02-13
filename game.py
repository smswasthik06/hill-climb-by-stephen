import pygame
import math
import random

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
FPS = 60
GRAVITY = 0.5
MAX_TILT_ANGLE = 75
MAX_LANDING_SPEED = 15
FUEL_CONSUMPTION = 0.05
JUMP_FORCE = 12
TERRAIN_SEGMENT_WIDTH = 20

# Colors
SKY_TOP = (135, 206, 250)
SKY_BOTTOM = (255, 255, 255)
GRASS_COLOR = (34, 139, 34)
SOIL_COLOR = (139, 90, 43)
COIN_COLOR = (255, 215, 0)
UI_BG = (0, 0, 0, 128)

class Particle:
    def __init__(self, x, y, vx, vy, color, lifetime, size=4):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.lifetime -= 1
        return self.lifetime > 0

class ParticleSystem:
    def __init__(self):
        self.particles = []
        
    def emit(self, x, y, count, color_range, speed_range, size=4):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(*speed_range)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice(color_range)
            lifetime = random.randint(20, 40)
            self.particles.append(Particle(x, y, vx, vy, color, lifetime, size))
            
    def update(self):
        self.particles = [p for p in self.particles if p.update()]
        
    def draw(self, screen, camera):
        for p in self.particles:
            alpha = int(255 * (p.lifetime / p.max_lifetime))
            size = max(1, int(p.size * (p.lifetime / p.max_lifetime)))
            screen_x, screen_y = camera.world_to_screen(p.x, p.y)
            if 0 <= screen_x < SCREEN_WIDTH and 0 <= screen_y < SCREEN_HEIGHT:
                pygame.draw.circle(screen, p.color, (int(screen_x), int(screen_y)), size)

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.shake_amount = 0
        self.shake_duration = 0
        
    def update(self, target_x, target_y):
        self.x += (target_x - self.x - 200) * 0.1
        self.y += (target_y - self.y - SCREEN_HEIGHT // 2) * 0.1
        
        if self.shake_duration > 0:
            self.shake_duration -= 1
            
    def world_to_screen(self, x, y):
        shake_x = random.uniform(-self.shake_amount, self.shake_amount) if self.shake_duration > 0 else 0
        shake_y = random.uniform(-self.shake_amount, self.shake_amount) if self.shake_duration > 0 else 0
        return x - self.x + shake_x, y - self.y + shake_y
        
    def shake(self, amount, duration):
        self.shake_amount = amount
        self.shake_duration = duration

class Terrain:
    def __init__(self):
        self.points = []
        self.generate_initial()
        
    def generate_initial(self):
        for i in range(-50, 200):
            x = i * TERRAIN_SEGMENT_WIDTH
            y = self.get_height_at(x)
            self.points.append((x, y))
            
    def get_height_at(self, x):
        base = 400
        difficulty = min(x / 5000, 2)
        wave1 = math.sin(x * 0.01) * 50 * (1 + difficulty)
        wave2 = math.sin(x * 0.03) * 25 * (1 + difficulty)
        wave3 = math.sin(x * 0.005) * 100 * (1 + difficulty)
        return base + wave1 + wave2 + wave3
        
    def update(self, camera_x):
        while self.points[-1][0] < camera_x + SCREEN_WIDTH + 500:
            last_x = self.points[-1][0]
            new_x = last_x + TERRAIN_SEGMENT_WIDTH
            new_y = self.get_height_at(new_x)
            self.points.append((new_x, new_y))
            
        while self.points[0][0] < camera_x - 500:
            self.points.pop(0)
            
    def get_ground_y(self, x):
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            if x1 <= x <= x2:
                t = (x - x1) / (x2 - x1)
                return y1 + (y2 - y1) * t
        return 400
        
    def get_slope_angle(self, x):
        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            if x1 <= x <= x2:
                return math.atan2(y2 - y1, x2 - x1)
        return 0
        
    def draw(self, screen, camera):
        visible_points = []
        for x, y in self.points:
            sx, sy = camera.world_to_screen(x, y)
            if -100 <= sx <= SCREEN_WIDTH + 100:
                visible_points.append((sx, sy))
                
        if len(visible_points) > 1:
            grass_points = visible_points + [(SCREEN_WIDTH + 100, SCREEN_HEIGHT + 100), (-100, SCREEN_HEIGHT + 100)]
            pygame.draw.polygon(screen, SOIL_COLOR, grass_points)
            pygame.draw.lines(screen, GRASS_COLOR, False, visible_points, 8)

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False
        self.radius = 15
        self.angle = 0
        
    def update(self):
        self.angle += 0.1
        
    def draw(self, screen, camera):
        if not self.collected:
            sx, sy = camera.world_to_screen(self.x, self.y)
            if -50 <= sx <= SCREEN_WIDTH + 50:
                scale = abs(math.cos(self.angle))
                width = int(self.radius * 2 * scale)
                if width > 2:
                    pygame.draw.ellipse(screen, COIN_COLOR, (sx - width // 2, sy - self.radius, width, self.radius * 2))
                    pygame.draw.ellipse(screen, (218, 165, 32), (sx - width // 2, sy - self.radius, width, self.radius * 2), 2)

class Island:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False
        self.size = 25
        
    def draw(self, screen, camera):
        if not self.collected:
            sx, sy = camera.world_to_screen(self.x, self.y)
            if -50 <= sx <= SCREEN_WIDTH + 50:
                # Island base (sand)
                pygame.draw.ellipse(screen, (194, 178, 128), (sx - self.size, sy - 10, self.size * 2, 20))
                # Palm tree trunk
                pygame.draw.rect(screen, (139, 90, 43), (sx - 3, sy - 20, 6, 15))
                # Palm leaves
                for angle in [0, math.pi/3, 2*math.pi/3, math.pi, 4*math.pi/3, 5*math.pi/3]:
                    leaf_x = sx + math.cos(angle) * 12
                    leaf_y = sy - 20 + math.sin(angle) * 8
                    pygame.draw.line(screen, (34, 139, 34), (sx, sy - 20), (leaf_x, leaf_y), 3)

class Obstacle:
    def __init__(self, x, y, type_name):
        self.x = x
        self.y = y
        self.type = type_name
        self.active = True
        self.size = 30
        
    def draw(self, screen, camera):
        if self.active:
            sx, sy = camera.world_to_screen(self.x, self.y)
            if -50 <= sx <= SCREEN_WIDTH + 50:
                if self.type == "fuel":
                    pygame.draw.rect(screen, (0, 200, 0), (sx - 15, sy - 25, 30, 40))
                    pygame.draw.rect(screen, (0, 255, 0), (sx - 12, sy - 22, 24, 34))
                    pygame.draw.rect(screen, (255, 255, 255), (sx - 8, sy - 18, 16, 10))

class Car:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.angle = 0
        self.angular_velocity = 0
        self.width = 70
        self.height = 60
        self.wheel_radius = 20
        self.wheel_base = 40
        self.front_wheel_angle = 0
        self.rear_wheel_angle = 0
        self.fuel = 100
        self.crashed = False
        self.on_ground = False
        self.can_jump = True
        self.suspension_front = 0
        self.suspension_rear = 0
        self.image = None
        self.load_image()
        
    def load_image(self):
        try:
            self.image = pygame.image.load("../eyevine01306955-2-removebg-preview.png")
            self.image = pygame.transform.scale(self.image, (80, 80))
        except:
            self.image = None
        
    def update(self, keys, terrain):
        if self.crashed:
            return
            
        # Input
        accelerating = False
        if keys[pygame.K_RIGHT] and self.fuel > 0:
            if self.on_ground:
                self.vx += 0.3
            self.fuel -= FUEL_CONSUMPTION
            accelerating = True
        if keys[pygame.K_LEFT] and self.on_ground:
            self.vx -= 0.2
        if keys[pygame.K_SPACE] and self.on_ground and self.can_jump:
            jump_boost = min(abs(self.vx) * 0.5, 5)
            self.vy = -(JUMP_FORCE + jump_boost)
            self.can_jump = False
        if keys[pygame.K_UP] and not self.on_ground:
            self.angular_velocity -= 0.005
        if keys[pygame.K_DOWN] and not self.on_ground:
            self.angular_velocity += 0.005
            
        # Physics
        self.vy += GRAVITY
        self.vx *= 0.99
        self.x += self.vx
        self.y += self.vy
        self.angle += self.angular_velocity
        self.angular_velocity *= 0.95
        
        # Wheel positions
        front_x = self.x + math.cos(self.angle) * self.wheel_base / 2
        front_y = self.y + math.sin(self.angle) * self.wheel_base / 2
        rear_x = self.x - math.cos(self.angle) * self.wheel_base / 2
        rear_y = self.y - math.sin(self.angle) * self.wheel_base / 2
        
        # Ground collision
        front_ground = terrain.get_ground_y(front_x)
        rear_ground = terrain.get_ground_y(rear_x)
        
        self.on_ground = False
        
        if front_y + self.wheel_radius > front_ground:
            front_y = front_ground - self.wheel_radius
            if self.vy > MAX_LANDING_SPEED:
                self.crashed = True
            self.on_ground = True
            
        if rear_y + self.wheel_radius > rear_ground:
            rear_y = rear_ground - self.wheel_radius
            if self.vy > MAX_LANDING_SPEED:
                self.crashed = True
            self.on_ground = True
            
        if self.on_ground:
            target_x = (front_x + rear_x) / 2
            target_y = (front_y + rear_y) / 2
            self.suspension_front = (front_ground - front_y - self.wheel_radius) * 0.3
            self.suspension_rear = (rear_ground - rear_y - self.wheel_radius) * 0.3
            self.x = target_x
            self.y = target_y - (self.suspension_front + self.suspension_rear) / 2
            self.can_jump = True
            self.angle = math.atan2(front_y - rear_y, front_x - rear_x)
            self.vy *= -0.3
            self.angular_velocity *= 0.5
        else:
            self.suspension_front *= 0.8
            self.suspension_rear *= 0.8
            
        # Tilt crash
        angle_deg = abs(math.degrees(self.angle) % 360)
        if angle_deg > 180:
            angle_deg = 360 - angle_deg
        if angle_deg > MAX_TILT_ANGLE and self.on_ground:
            self.crashed = True
            
        # Wheel rotation
        if self.on_ground:
            self.front_wheel_angle += self.vx * 0.1
            self.rear_wheel_angle += self.vx * 0.1
            
        return accelerating
        
    def draw(self, screen, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        
        # Draw character image if loaded
        if self.image:
            rotated_image = pygame.transform.rotate(self.image, -math.degrees(self.angle))
            image_rect = rotated_image.get_rect(center=(int(sx), int(sy - 10)))
            screen.blit(rotated_image, image_rect)
        else:
            # Fallback: Draw simple rectangle if image not found
            body_points = []
            for dx, dy in [(-25, -20), (25, -20), (25, 10), (-25, 10)]:
                rx = dx * math.cos(self.angle) - dy * math.sin(self.angle)
                ry = dx * math.sin(self.angle) + dy * math.cos(self.angle)
                body_points.append((sx + rx, sy + ry))
            pygame.draw.polygon(screen, (100, 100, 200), body_points)
        
        # Wheels with suspension
        for i, offset in enumerate([-self.wheel_base / 2, self.wheel_base / 2]):
            susp = self.suspension_rear if i == 0 else self.suspension_front
            wx = sx + math.cos(self.angle) * offset
            wy = sy + math.sin(self.angle) * offset + susp
            
            # Suspension
            spring_top_x = sx + math.cos(self.angle) * offset
            spring_top_y = sy + math.sin(self.angle) * offset + 10
            pygame.draw.line(screen, (150, 150, 150), (spring_top_x, spring_top_y), (wx, wy), 2)
            
            # Wheels
            pygame.draw.circle(screen, (50, 50, 50), (int(wx), int(wy)), self.wheel_radius)
            pygame.draw.circle(screen, (30, 30, 30), (int(wx), int(wy)), self.wheel_radius - 3)
            pygame.draw.circle(screen, (80, 80, 80), (int(wx), int(wy)), self.wheel_radius - 6)
            
            # Spokes
            angle = self.front_wheel_angle if offset > 0 else self.rear_wheel_angle
            for spoke_angle in [angle, angle + math.pi / 4, angle + math.pi / 2, angle + 3 * math.pi / 4,
                               angle + math.pi, angle + 5 * math.pi / 4, angle + 3 * math.pi / 2, angle + 7 * math.pi / 4]:
                spoke_x = wx + math.cos(spoke_angle) * (self.wheel_radius - 8)
                spoke_y = wy + math.sin(spoke_angle) * (self.wheel_radius - 8)
                pygame.draw.line(screen, (150, 150, 150), (wx, wy), (spoke_x, spoke_y), 1)

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Hill Climb Racing - Custom Character")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.engine_sound_playing = False
        self.reset()
        
    def reset(self):
        self.car = Car(100, 300)
        self.terrain = Terrain()
        self.camera = Camera()
        self.particles = ParticleSystem()
        self.coins = []
        self.islands = []
        self.obstacles = []
        self.distance = 0
        self.score = 0
        self.coin_count = 0
        self.running = True
        self.game_over = False
        self.spawn_timer = 0
        self.milestone_message = ""
        self.milestone_timer = 0
        self.last_milestone = 0
        
        # Spawn initial items
        for i in range(10):
            x = random.randint(200, 5000)
            y = self.terrain.get_ground_y(x) - 50
            self.coins.append(Coin(x, y))
            
        for i in range(5):
            x = random.randint(300, 5000)
            y = self.terrain.get_ground_y(x) - 40
            self.obstacles.append(Obstacle(x, y, "fuel"))
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over:
                    self.reset()
                    self.game_over = False
                    
    def update(self):
        if self.game_over:
            return
            
        keys = pygame.key.get_pressed()
        accelerating = self.car.update(keys, self.terrain)
        
        speed = abs(self.car.vx)
        
        if accelerating and self.car.on_ground:
            exhaust_x = self.car.x - math.cos(self.car.angle) * 35
            exhaust_y = self.car.y - math.sin(self.car.angle) * 35
            
            if speed < 2:
                smoke_colors = [(0, 200, 0), (50, 255, 50), (100, 255, 100)]
                particle_count = 5
                particle_size = 8
            elif speed < 5:
                smoke_colors = [(255, 255, 0), (255, 200, 0), (200, 200, 0)]
                particle_count = 8
                particle_size = 12
            else:
                smoke_colors = [(255, 0, 0), (255, 100, 0), (200, 0, 0)]
                particle_count = 12
                particle_size = 16
                
            self.particles.emit(exhaust_x, exhaust_y, particle_count, smoke_colors, (2, 5), particle_size)
            
        self.terrain.update(self.camera.x)
        self.camera.update(self.car.x, self.car.y)
        self.particles.update()
        
        # Update distance and score
        self.distance = max(0, int(self.car.x / 10))
        self.score = self.distance + self.coin_count * 10
        
        # Check for milestones every 100 meters
        current_milestone = (self.distance // 100) * 100
        if current_milestone > self.last_milestone and current_milestone > 0:
            self.last_milestone = current_milestone
            self.milestone_message = f"I VISITED EPSTEIN ISLAND"
            self.milestone_timer = 180
            # Spawn island at current position
            island_x = self.car.x + 100
            island_y = self.terrain.get_ground_y(island_x) - 30
            self.islands.append(Island(island_x, island_y))
        
        # Update milestone timer
        if self.milestone_timer > 0:
            self.milestone_timer -= 1
        
        # Coin collection
        for coin in self.coins:
            if not coin.collected:
                coin.update()
                dist = math.sqrt((self.car.x - coin.x) ** 2 + (self.car.y - coin.y) ** 2)
                if dist < 30:
                    coin.collected = True
                    self.coin_count += 1
        
        # Island collection
        for island in self.islands:
            if not island.collected:
                dist = math.sqrt((self.car.x - island.x) ** 2 + (self.car.y - island.y) ** 2)
                if dist < 40:
                    island.collected = True
                    
        # Obstacle interaction
        for obs in self.obstacles:
            if obs.active:
                dist = math.sqrt((self.car.x - obs.x) ** 2 + (self.car.y - obs.y) ** 2)
                if dist < 40:
                    if obs.type == "fuel":
                        self.car.fuel = min(100, self.car.fuel + 30)
                        obs.active = False
                        
        # Spawn new items
        self.spawn_timer += 1
        if self.spawn_timer > 60:
            self.spawn_timer = 0
            spawn_x = self.camera.x + SCREEN_WIDTH + random.randint(100, 500)
            spawn_y = self.terrain.get_ground_y(spawn_x) - 50
            
            if random.random() < 0.7:
                self.coins.append(Coin(spawn_x, spawn_y))
            else:
                self.obstacles.append(Obstacle(spawn_x, spawn_y, "fuel"))
                
        # Check game over
        if self.car.crashed or self.car.fuel <= 0:
            self.game_over = True
            if self.car.crashed:
                self.particles.emit(self.car.x, self.car.y, 50, [(100, 100, 100), (150, 150, 150), (200, 200, 200)], (2, 6))
                self.camera.shake(15, 30)
                
    def draw_gradient_sky(self):
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t)
            g = int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t)
            b = int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
            
    def draw_mountains(self):
        for layer in range(3):
            offset = self.camera.x * (0.1 + layer * 0.05)
            points = []
            for x in range(-100, SCREEN_WIDTH + 100, 50):
                world_x = x + offset
                height = 200 + layer * 50 + math.sin(world_x * 0.005) * 50 + math.sin(world_x * 0.01) * 30
                points.append((x, height))
            points.append((SCREEN_WIDTH + 100, SCREEN_HEIGHT))
            points.append((-100, SCREEN_HEIGHT))
            color_val = 100 - layer * 20
            pygame.draw.polygon(self.screen, (color_val, color_val, color_val + 50), points)
            
    def draw_hud(self):
        # Fuel bar
        fuel_width = 200
        fuel_height = 30
        fuel_x = 20
        fuel_y = 20
        pygame.draw.rect(self.screen, (50, 50, 50), (fuel_x, fuel_y, fuel_width, fuel_height))
        fuel_fill = int((self.car.fuel / 100) * fuel_width)
        fuel_color = (0, 255, 0) if self.car.fuel > 30 else (255, 0, 0)
        pygame.draw.rect(self.screen, fuel_color, (fuel_x, fuel_y, fuel_fill, fuel_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (fuel_x, fuel_y, fuel_width, fuel_height), 2)
        
        fuel_text = self.small_font.render(f"Fuel: {int(self.car.fuel)}%", True, (255, 255, 255))
        self.screen.blit(fuel_text, (fuel_x + 5, fuel_y + 5))
        
        # Stats
        stats_y = 60
        speed = abs(self.car.vx)
        speed_text = self.small_font.render(f"Speed: {int(speed * 10)} km/h", True, (255, 255, 255))
        self.screen.blit(speed_text, (20, stats_y))
        
        dist_text = self.small_font.render(f"Distance: {self.distance} m", True, (255, 255, 255))
        self.screen.blit(dist_text, (20, stats_y + 30))
        
        coin_text = self.small_font.render(f"Coins: {self.coin_count}", True, (255, 215, 0))
        self.screen.blit(coin_text, (20, stats_y + 60))
        
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (20, stats_y + 90))
        
        difficulty = min(int(self.car.x / 1000) + 1, 10)
        diff_text = self.small_font.render(f"Level: {difficulty}", True, (255, 255, 255))
        self.screen.blit(diff_text, (20, stats_y + 130))
        
    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        title = self.font.render("GAME OVER", True, (255, 0, 0))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(title, title_rect)
        
        reason = "Out of Fuel!" if self.car.fuel <= 0 else "Crashed!"
        reason_text = self.small_font.render(reason, True, (255, 255, 255))
        reason_rect = reason_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(reason_text, reason_rect)
        
        final_score = self.font.render(f"Final Score: {self.score}", True, (255, 215, 0))
        score_rect = final_score.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(final_score, score_rect)
        
        final_dist = self.small_font.render(f"Distance: {self.distance} m", True, (255, 255, 255))
        dist_rect = final_dist.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        self.screen.blit(final_dist, dist_rect)
        
        final_coins = self.small_font.render(f"Coins: {self.coin_count}", True, (255, 255, 255))
        coins_rect = final_coins.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
        self.screen.blit(final_coins, coins_rect)
        
        restart = self.font.render("Press R to Restart", True, (0, 255, 0))
        restart_rect = restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
        self.screen.blit(restart, restart_rect)
        
    def draw(self):
        self.draw_gradient_sky()
        self.draw_mountains()
        self.terrain.draw(self.screen, self.camera)
        
        for coin in self.coins:
            coin.draw(self.screen, self.camera)
        
        for island in self.islands:
            island.draw(self.screen, self.camera)
            
        for obs in self.obstacles:
            obs.draw(self.screen, self.camera)
            
        self.car.draw(self.screen, self.camera)
        self.particles.draw(self.screen, self.camera)
        self.draw_hud()
        
        # Draw milestone message in center
        if self.milestone_timer > 0:
            alpha = min(255, self.milestone_timer * 2)
            big_font = pygame.font.Font(None, 72)
            text = big_font.render(self.milestone_message, True, (255, 0, 0))
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            
            # Background for text
            bg_rect = text_rect.inflate(40, 20)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
            bg_surface.set_alpha(min(200, alpha))
            bg_surface.fill((0, 0, 0))
            self.screen.blit(bg_surface, bg_rect)
            
            self.screen.blit(text, text_rect)
        
        if self.game_over:
            self.draw_game_over()
            
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
            
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
