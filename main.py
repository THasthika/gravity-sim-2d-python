from typing import Optional
import pygame
import random
import math
from vector_2d import Vec2d

WINDOW_WIDTH, WINDOW_HEIGHT = 800, 800
OUTER_LIMITS = (-2*max(WINDOW_WIDTH, WINDOW_HEIGHT), 2*max(WINDOW_WIDTH, WINDOW_HEIGHT))
FPS = 30
SURFACE_COLOR = (0, 0, 0)
G = 20000

width, height = 0, 0


def get_random_value_from_range(rng):
    (l, h) = rng
    return random.randint(l, h)


def generate_planet_color(alpha: Optional[int] = None):

    valid_range = (100, 200)

    r = get_random_value_from_range(valid_range)
    g = get_random_value_from_range(valid_range)
    b = get_random_value_from_range(valid_range)

    if alpha is None:
        return (r, g, b)
    return (r, g, b, alpha)


class Planet(pygame.sprite.Sprite):

    def __init__(self, position: Vec2d, radius: float, mass: float,
                 velocity: Optional[Vec2d] = None):
        super().__init__()

        self.radius = radius
        self.mass = mass
        self.position = position
        self.color = generate_planet_color()
        self.velocity = velocity if velocity is not None else Vec2d(0, 0)
        self.acceleration = Vec2d(0, 0)
        self.should_remove = False
        self.fixed = False

        self.update_dimensions()

    def update_dimensions(self):

        sz = int(self.radius * 2)
        self.image = pygame.Surface([sz, sz],
                                    pygame.SRCALPHA, 32)

        # self.image.fill((255, 255, 255, 0))

        pygame.draw.circle(self.image, self.color,
                           (self.radius, self.radius), self.radius)

        # self.image.fill(CELL_BORDER_COLOR)
        # self.image.set_colorkey(CELL_BORDER_COLOR)

        self.rect = self.image.get_rect()
        self.rect.centerx = self.position.x
        self.rect.centery = self.position.y

    def update(self, dt: float):

        if self.fixed:
            self.velocity.x = 0
            self.velocity.y = 0
        else:
            self.velocity += self.acceleration * dt

        self.position += self.velocity * dt

        self.rect.centerx = self.position.x
        self.rect.centery = self.position.y

        if self.rect.centerx < OUTER_LIMITS[0] or self.rect.centerx > OUTER_LIMITS[1]:
            self.should_remove = True

        if self.rect.centery < OUTER_LIMITS[0] or self.rect.centery > OUTER_LIMITS[1]:
            self.should_remove = True

        # if self.rect.centerx < 0 or self.rect.centerx > width:
        #     self.velocity.x *= -1

        # if self.rect.centery < 0 or self.rect.centery > height:
        #     self.velocity.y *= -1

    def clear_forces(self):

        self.acceleration.x = 0
        self.acceleration.y = 0

    def check_collision(self, other_planet):

        d = self.position.get_distance(other_planet.position)
        if d > self.radius + other_planet.radius:
            return False

        self_volume = math.pi * self.radius ** 2
        other_volume = math.pi * other_planet.radius ** 2

        self_density = self.mass / self_volume
        other_density = other_planet.mass / other_volume

        new_density = (self_density + other_density) / 2
        new_mass = self.mass + other_planet.mass
        new_volume = new_mass / new_density
        new_radius = math.sqrt(new_volume / math.pi)
        new_color = self.color if self.mass > other_planet.mass else other_planet.color

        if self.fixed or other_planet.fixed:
            # for collision with fixed planets
            fixed_planet = self if self.fixed else other_planet
            other_planet = self if not self.fixed else other_planet
            
            fixed_planet.mass = new_mass
            fixed_planet.radius = new_radius
            fixed_planet.color = new_color
            fixed_planet.update_dimensions()

            other_planet.should_remove = True

            return True

        # new_radius = self.radius if self.radius > other_planet.radius \
        #     else other_planet.radius

        self_ke = self.mass * (self.velocity)
        other_ke = other_planet.mass * (other_planet.velocity)
        new_ke = self_ke + other_ke
        new_velocity = (new_ke / new_mass)

        other_planet.should_remove = True

        self.position = (self.mass * self.position + other_planet.mass * other_planet.position) / (self.mass + other_planet.mass)
        self.radius = new_radius
        self.mass = new_mass
        self.velocity = new_velocity
        self.color = new_color

        self.update_dimensions()

        return True

    def update_forces(self, other_planet):

        d = self.position.get_dist_sqrd(other_planet.position)

        direction_v = (self.position - other_planet.position).normalized()

        self_a = ((other_planet.mass * G) / d) * -direction_v
        other_a = ((self.mass * G) / d) * direction_v

        self.acceleration += self_a
        other_planet.acceleration += other_a


class PlanetTrail(pygame.sprite.Sprite):

    MAX_POINTS = 1000
    D_CHANGE = 1

    def __init__(self, planet: Planet) -> None:
        super().__init__()
        self.planet = planet
        self.color = self.planet.color
        self.points = [Vec2d(self.planet.position)]
        self.min_x = 0
        self.min_y = 0
        self.max_x = 0
        self.max_y = 0
        self.update_bounds()
        self.update_sprite()

    def update_bounds(self):

        (min_x, max_x, min_y, max_y) = (self.points[0].x, self.points[0].x, self.points[0].y, self.points[0].y)

        for i in range(1, len(self.points)):
            p = self.points[i]
            if p.x < min_x:
                min_x = p.x
            if p.x > max_x:
                max_x = p.x
            if p.y < min_y:
                min_y = p.y
            if p.y > max_y:
                max_y = p.y

        self.max_x = max_x
        self.max_y = max_y
        self.min_x = min_x
        self.min_y = min_y

    def update(self, dt):

        if self.planet.should_remove:
            self.kill()

        if self.points[-1].get_dist_sqrd(self.planet.position) <= PlanetTrail.D_CHANGE:
            return
        
        if len(self.points) >= PlanetTrail.MAX_POINTS:
            self.points.pop(0)
        
        new_point = Vec2d(self.planet.position)
        self.points.append(new_point)

        self.update_bounds()
        self.update_sprite()

    def update_sprite(self):
        self.image = pygame.Surface([self.max_x - self.min_x, self.max_y - self.min_y], pygame.SRCALPHA, 32)

        # self.image.fill((255, 255, 255, 0))

        min_p = Vec2d(self.min_x, self.min_y)

        if len(self.points) > 1:
            points = map(lambda x: (x.x, x.y), map(lambda x: x - min_p, self.points))
            pygame.draw.lines(self.image, self.color, False, list(points))

        # self.image.fill(CELL_BORDER_COLOR)
        # self.image.set_colorkey(CELL_BORDER_COLOR)

        self.rect = self.image.get_rect()
        self.rect.x = min_p.x
        self.rect.y = min_p.y


pygame.init()

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
width = pygame.display.Info().current_w
height = pygame.display.Info().current_h

clock = pygame.time.Clock()

running = True

planets = pygame.sprite.Group()
planet_trails = pygame.sprite.Group()

# p = Planet(Vec2d(20, 20), 12.0, 1)
# planets.add(p)

# p = Planet(Vec2d(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2), 10, 100)
# p.fixed = True
# planets.add(p)

# for i in range(10):
#     p = Planet(Vec2d(random.randint(10, 700), random.randint(10, 700)), 1, 1)
#     planets.add(p)


class PlanetCreator():

    def __init__(self, init_pos) -> None:
        
        self.init_pos = Vec2d(init_pos)

    def on_release(self, pos):

        self.release_pos = Vec2d(pos)

        velocity_vector = self.init_pos - self.release_pos

        p = Planet(self.init_pos, 1, 1, velocity_vector)
        p_trail = PlanetTrail(p)

        planets.add(p)
        planet_trails.add(p_trail)


planet_creator = None


def handle_input(event):
    global running
    global planet_creator

    if event.type == pygame.QUIT:
        running = False

    if event.type == pygame.MOUSEBUTTONDOWN:
        planet_creator = PlanetCreator(event.pos)

    # if event.type == pygame.MOUSEMOTION:
    #     if planet_creator is not None:
    #         p = event.pos

    if event.type == pygame.MOUSEBUTTONUP:
        if planet_creator is not None:
            planet_creator.on_release(event.pos)


def update(dt):

    for p in planets:
        p.clear_forces()

    for (i, px) in enumerate(planets):
        
        if px.should_remove:
            continue

        for (j, py) in enumerate(planets):
            
            if j == i:
                break

            if py.should_remove:
                continue
            
            if px.check_collision(py):
                continue

            px.update_forces(py)

    for p in planets:

        if p.should_remove:
            p.kill()
            continue

        p.update(dt)

    for pt in planet_trails:

        pt.update(dt)


def render():
    planets.draw(screen)
    planet_trails.draw(screen)


while running:

    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        handle_input(event)

    update(dt)

    screen.fill(SURFACE_COLOR)
    render()
    
    pygame.display.flip()


pygame.quit()
