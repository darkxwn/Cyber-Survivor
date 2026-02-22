import pygame
from systems import *
import os
import sys

class Engine:
    def __init__(self):
        pygame.display.set_caption("CYBER SURVIVOR")
        self.clock = pygame.time.Clock()
        self.dt = 0
        
        # --- ЭКРАН ЗАГРУЗКИ ---
        self._draw_loading_screen()
        
        self.save_system = SaveSystem()
        
        # Звуки и музыка
        self.sound_manager = SoundManager()
        
        # Курсор управляется через настройки
        self.cursor_size = 20
        cursor_mode = "game"  # will be updated from settings
        if cursor_mode == "system":
            pygame.mouse.set_visible(True)
        else:
            pygame.mouse.set_visible(False)
        
        # Загрузка иконок
        self.icons = {}
        self.load_icons()
        
        # Кэш градиентного фона для подменю (рендерится 1 раз)
        self._menu_bg_cache = None
        self._menu_bg_size = (0, 0)
        
        # Шрифты
        self.font_huge = pygame.font.Font(None, 88)
        self.font_large = pygame.font.Font(None, 60)
        self.font_medium = pygame.font.Font(None, 40)
        self.font_small = pygame.font.Font(None, 28)
        self.font_tiny = pygame.font.Font(None, 22)
        
        self.state = GameState.MENU
        self.menu_page = "main"
        self.game_mode = GameMode.WAVES  # По умолчанию режим волн
        
        self.reset_game()
        
        # UI состояния
        self.pause_click_handled = False
        self.level_up_click_handled = False
        self.rebinding_key = None
        self.achievements_scroll_offset = 0  # Прокрутка для меню достижений
        self.show_stats_reset_confirmation = False  # Подтверждение сброса статистики
        
        # Анимации меню (5 & 6)
        self.menu_time = 0
        self.button_press_effect = {}  # {button_id: time_pressed}
        self.menu_particles = []  # Динамические частицы фона
        
        # Система волн
        wave_break = self.save_system.data["settings"].get("wave_break_duration", 10)
        endless_mode = (self.game_mode == GameMode.ENDLESS)
        self.wave_system = WaveSystem(wave_break, endless_mode)
        
        # Запуск музыки в меню
        self.sound_manager.play_music("menu_theme.ogg")
    
    def _draw_loading_screen(self):
        """Красивый экран загрузки при запуске"""
        font_title = pygame.font.Font(None, 100)
        font_sub = pygame.font.Font(None, 34)
        font_tiny = pygame.font.Font(None, 22)
        
        steps = ["Инициализация системы...", "Загрузка ресурсов...", "Построение мира...", "Готово!"]
        for idx, step in enumerate(steps):
            # Градиентный фон — тёмный киберпанк
            for i in range(HEIGHT):
                r = int(3 + 12 * i / HEIGHT)
                g = int(5 + 10 * i / HEIGHT)
                b = int(15 + 22 * i / HEIGHT)
                pygame.draw.line(screen, (r, g, b), (0, i), (WIDTH, i))
            
            # Сетка фона
            for gx in range(0, WIDTH, 60):
                pygame.draw.line(screen, (15, 20, 35), (gx, 0), (gx, HEIGHT), 1)
            for gy in range(0, HEIGHT, 60):
                pygame.draw.line(screen, (15, 20, 35), (0, gy), (WIDTH, gy), 1)
            
            # Декоративные угловые линии
            corner_len = 80
            corner_col = (0, 255, 204)
            cx, cy = WIDTH // 2, HEIGHT // 2
            # Уголки рамки
            for bx, by, sx, sy in [
                (cx - 325, cy - 150, 1, 1),
                (cx + 325, cy - 150, -1, 1),
                (cx - 325, cy + 150, 1, -1),
                (cx + 325, cy + 150, -1, -1),
            ]:
                pygame.draw.line(screen, corner_col, (bx, by), (bx + sx * corner_len, by), 2)
                pygame.draw.line(screen, corner_col, (bx, by), (bx, by + sy * corner_len), 2)
            
            # Название с глоу-эффектом
            title_txt = "CYBER SURVIVOR"
            for gi in range(4, 0, -1):
                alpha = 25 - gi * 5
                glow_color = (0, int(255 * alpha / 25), int(204 * alpha / 25))
                gt = font_title.render(title_txt, True, glow_color)
                screen.blit(gt, gt.get_rect(center=(WIDTH // 2 + gi, HEIGHT // 2 - 65 + gi)))
            title = font_title.render(title_txt, True, (0, 255, 204))
            screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 65)))
            
            # Прогресс бар с секциями
            bar_w = 500
            bar_h = 10
            bar_x = WIDTH // 2 - bar_w // 2
            bar_y = HEIGHT // 2 + 35
            progress = (idx + 1) / len(steps)
            
            # Фон бара
            pygame.draw.rect(screen, (20, 25, 40), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), border_radius=5)
            pygame.draw.rect(screen, (30, 38, 55), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
            
            # Заполнение с градиентом
            fill_w = int(bar_w * progress)
            if fill_w > 0:
                for fi in range(fill_w):
                    t = fi / bar_w
                    r = int(0 + 0 * t)
                    g = int(200 + 55 * t)
                    b = int(180 + 24 * t)
                    pygame.draw.line(screen, (r, g, b), (bar_x + fi, bar_y + 1), (bar_x + fi, bar_y + bar_h - 1))
            
            # Свечение бара
            pygame.draw.rect(screen, (0, 255, 204), (bar_x, bar_y, fill_w, bar_h), 2, border_radius=4)
            
            # Точки-разделители
            for di in range(1, len(steps)):
                dx = bar_x + int(bar_w * di / len(steps))
                col = (0, 255, 204) if di <= idx + 1 else (40, 50, 70)
                pygame.draw.circle(screen, col, (dx, bar_y + bar_h // 2), 4)
            
            # Текст шага
            sub = font_sub.render(step, True, (180, 200, 230))
            screen.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 65)))
            
            # Версия
            ver = font_tiny.render("v4.3 — Enhanced Edition", True, (60, 70, 100))
            screen.blit(ver, ver.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100)))
            
            pygame.display.flip()
            pygame.time.delay(300)
        
        pygame.time.delay(150)

    def load_icons(self):
        """Загрузка иконок из assets/icons"""
        icon_dir = os.path.join(os.path.dirname(__file__), "../assets/", "icons")
        
        if not os.path.exists(icon_dir):
            return  # Если папки нет, работаем без иконок
        
        icon_files = {
            # Главное меню
            "play": "play.png",
            "achievements": "achievements.png",
            "knowledge": "knowledge.png",
            "modules": "modules.png",
            "skins": "skins.png",
            "settings": "settings.png",
            "stats": "stats.png",
            "quit": "quit.png",
            
            # Модули
            "health": "health.png",
            "damage": "damage.png",
            "speed": "speed.png",
            "firerate": "firerate.png",
            "crit": "crit.png",
            
            # Управление
            "arrow_up": "arrow_up.png",
            "arrow_down": "arrow_down.png",
            "arrow_left": "arrow_left.png",
            "arrow_right": "arrow_right.png",
            "dash": "dash.png",
            "autofire": "autofire.png",
            
            # Режимы
            "waves": "waves.png",
            "endless": "endless.png",
            
            # Статистика
            "games": "games.png",
            "kills": "kills.png",
            "time": "time.png",
            "score": "score.png",
            "besttime": "besttime.png",
            "level": "level.png",
            "wave": "wave.png",
            
            # Дополнительно
            "currency": "currency.png",
            "lock": "lock.png",
        }
        
        for key, filename in icon_files.items():
            try:
                path = os.path.join(icon_dir, filename)
                if os.path.exists(path):
                    icon = pygame.image.load(path).convert_alpha()
                    icon = pygame.transform.scale(icon, (48, 48))  # Стандартный размер
                    self.icons[key] = icon
            except Exception as e:
                pass  # Игнорируем ошибки загрузки отдельных иконок
    
    def draw_icon(self, icon_name, x, y, size=48):
        """Отрисовка иконки если есть, иначе возвращает False"""
        if icon_name in self.icons:
            icon = self.icons[icon_name]
            if icon.get_width() != size:
                icon = pygame.transform.scale(icon, (size, size))
            screen.blit(icon, (x - size // 2, y - size // 2))
            return True
        return False
    
    def draw_cursor(self):
        """Кастомный курсор-прицел (только если включён игровой режим)"""
        cursor_mode = self.save_system.data["settings"].get("cursor_mode", "game")
        if cursor_mode == "system":
            pygame.mouse.set_visible(True)
            return
        pygame.mouse.set_visible(False)
        mouse_pos = pygame.mouse.get_pos()
        x, y = mouse_pos
        
        # Внешний круг (прицел)
        pygame.draw.circle(screen, COLORS["player"], (x, y), self.cursor_size, 2)
        
        # Внутренний круг
        pygame.draw.circle(screen, COLORS["player"], (x, y), 3)
        
        # Крестик
        line_length = self.cursor_size + 5
        pygame.draw.line(screen, COLORS["player"], (x - line_length, y), (x - self.cursor_size - 2, y), 2)
        pygame.draw.line(screen, COLORS["player"], (x + self.cursor_size + 2, y), (x + line_length, y), 2)
        pygame.draw.line(screen, COLORS["player"], (x, y - line_length), (x, y - self.cursor_size - 2), 2)
        pygame.draw.line(screen, COLORS["player"], (x, y + self.cursor_size + 2), (x, y + line_length), 2)
    
    def _draw_submenu_bg(self):
        """Рисует кэшированный градиентный фон для подменю (оптимизация)"""
        if self._menu_bg_cache is None or self._menu_bg_size != (WIDTH, HEIGHT):
            self._menu_bg_size = (WIDTH, HEIGHT)
            self._menu_bg_cache = pygame.Surface((WIDTH, HEIGHT))
            for _i in range(HEIGHT):
                _p = _i / HEIGHT
                self._menu_bg_cache.fill((int(7+14*_p), int(9+18*_p), int(18+30*_p)), (0, _i, WIDTH, 1))
        screen.blit(self._menu_bg_cache, (0, 0))
        # Dot overlay
        for _dx in range(0, WIDTH + 50, 50):
            for _dy in range(0, HEIGHT + 50, 50):
                pygame.draw.circle(screen, (20, 26, 44), (_dx, _dy), 2)

    # ===== UI HELPERS =====
    CONTAINER_W = 1100
    CONTAINER_Y_START = 130
    CONTAINER_PADDING = 15
    
    def ui_draw_title(self, text: str, y: int = 60):
        """Стандартный заголовок подменю с свечением"""
        title = self.font_large.render(text, True, COLORS["player"])
        title_rect = title.get_rect(center=(WIDTH // 2, y))
        glow_surf = pygame.Surface((title_rect.width + 40, title_rect.height + 40), pygame.SRCALPHA)
        for i in range(3):
            alpha = 35 - i * 10
            glow_t = self.font_large.render(text, True, (*COLORS["player_glow"], alpha))
            glow_surf.blit(glow_t, (20 + i * 2, 20 + i * 2))
        screen.blit(glow_surf, (title_rect.x - 20, title_rect.y - 20))
        screen.blit(title, title_rect)
        return title_rect
    
    def ui_container(self, w: int = None, x: int = None, y: int = None, h: int = None) -> tuple:
        """Рисует стандартный контейнер, возвращает (rect, cont_x, cont_y, cont_w, cont_h)"""
        cont_w = w or self.CONTAINER_W
        cont_h = h or (HEIGHT - 280)
        cont_x = x if x is not None else (WIDTH // 2 - cont_w // 2)
        cont_y = y if y is not None else self.CONTAINER_Y_START
        cont_rect = pygame.Rect(cont_x, cont_y, cont_w, cont_h)
        pygame.draw.rect(screen, (15, 18, 25), cont_rect, border_radius=12)
        pygame.draw.rect(screen, COLORS["card_border"], cont_rect, 2, border_radius=12)
        return cont_rect, cont_x, cont_y, cont_w, cont_h
    
    def ui_button(self, rect: pygame.Rect, text: str, color=None, hover_color=None, 
                  font=None, is_hover: bool = False, border_w: int = 2) -> None:
        """Рисует стандартную кнопку"""
        color = color or COLORS["card_border"]
        hover_color = hover_color or COLORS["player"]
        font = font or self.font_small
        bc = hover_color if is_hover else color
        bg = (40, 50, 68) if is_hover else (28, 34, 50)
        pygame.draw.rect(screen, bg, rect, border_radius=10)
        pygame.draw.rect(screen, bc, rect, border_w, border_radius=10)
        t = font.render(text, True, bc)
        screen.blit(t, t.get_rect(center=rect.center))
    
    def ui_scrollbar(self, cont_x: int, cont_y: int, cont_w: int, cont_h: int,
                     total_h: int, scroll: int) -> None:
        """Рисует скроллбар если нужен"""
        max_scroll = max(0, total_h - cont_h)
        if max_scroll > 0 and total_h > 0:
            sb_h = max(30, int((cont_h / total_h) * cont_h))
            sb_y = cont_y + 2 + int((scroll / max_scroll) * (cont_h - sb_h - 4))
            sb_y = max(cont_y + 2, min(cont_y + cont_h - sb_h - 2, sb_y))
            pygame.draw.rect(screen, COLORS["player"], 
                           (cont_x + cont_w - 12, sb_y, 8, sb_h), border_radius=4)

    def reset_game(self):
        modules = self.save_system.data["modules"]
        skin = self.save_system.data["current_skin"]
        self.player = Player(modules, skin)
        self.enemies: List[Enemy] = []
        self.bullets: List[Bullet] = []
        self.enemy_bullets: List[dict] = []   # Снаряды врагов
        self.exp_gems: List[pygame.Vector2] = []
        self.particle_system = ParticleSystem()
        
        self.cam = pygame.Vector2(0, 0)
        self.score = 0
        self.kills = 0
        self.time_survived = 0
        
        self.last_enemy_spawn = 0
        self.spawn_rate = 1000
        self.dash_count = 0  # Счётчик рывков для достижения
        self._miniboss_spawned_this_wave = False
        self.ability_cooldown = 0  # Кулдаун активной способности (мс)
        self.ability_active_timer = 0  # Таймер активного эффекта
        
        # Сброс системы волн
        wave_break = self.save_system.data["settings"].get("wave_break_duration", 10)
        endless_mode = (self.game_mode == GameMode.ENDLESS)
        self.wave_system = WaveSystem(wave_break, endless_mode)
        self.wave_system.start_wave()
        
        # Перки для level up
        if hasattr(self, 'current_perks'):
            delattr(self, 'current_perks')
    
    def update_player_input(self):
        keys = pygame.key.get_pressed()
        controls = self.save_system.data["controls"]
        
        move = pygame.Vector2(0, 0)
        if keys[controls["left"]]:
            move.x -= 1
        if keys[controls["right"]]:
            move.x += 1
        if keys[controls["up"]]:
            move.y -= 1
        if keys[controls["down"]]:
            move.y += 1
        
        if move.length() > 0:
            self.player.pos += move.normalize() * self.player.speed
        
        self.player.pos += self.player.velocity
        
        # Dash
        if keys[controls["dash"]]:
            if self.player.dash(move):
                self.dash_count += 1
                self.particle_system.emit(self.player.pos, 20, self.player.color, (5, 12))
                # Звук дэша
                self.sound_manager.play_sound("dash")
    
    def update_shooting(self):
        auto_fire = self.save_system.data["settings"]["auto_fire"]
        
        # Автострельба или зажатие ЛКМ
        should_shoot = False
        if auto_fire:
            # При автострельбе стреляем всегда
            should_shoot = True
        else:
            # При ручной стрельбе только при зажатой ЛКМ
            should_shoot = pygame.mouse.get_pressed()[0]
        
        if should_shoot:
            now = pygame.time.get_ticks()
            if now - self.player.last_shot > self.player.fire_rate:
                self.player.last_shot = now
                
                m_pos = pygame.mouse.get_pos()
                rel = pygame.Vector2(m_pos) - (self.player.pos + self.cam)
                if rel.length() > 0:
                    base_angle = math.degrees(math.atan2(rel.y, rel.x))
                    
                    twin = getattr(self.player, 'twin_shot', 0)
                    total_bullets = self.player.multishot + twin
                    
                    # Параллельные выстрелы: все летят в одном направлении, но с боковым смещением
                    if total_bullets > 1:
                        # Перпендикулярное направление для смещения
                        perp_angle = math.radians(base_angle + 90)
                        perp = pygame.Vector2(math.cos(perp_angle), math.sin(perp_angle))
                        spacing = 14  # пикселей между пулями
                        offsets = []
                        for i in range(total_bullets):
                            offset_dist = (i - (total_bullets - 1) / 2) * spacing
                            offsets.append(perp * offset_dist)
                    else:
                        offsets = [pygame.Vector2(0, 0)]
                    
                    for offset in offsets:
                        is_crit = random.random() < self.player.crit_chance
                        dmg = int(self.player.dmg * (self.player.crit_multiplier if is_crit else 1))
                        self.bullets.append(Bullet(
                            self.player.pos + offset, base_angle, self.player.bullet_speed,
                            dmg, self.player.piercing, self.player.bullet_size,
                            self.player.bullet_lifetime, is_crit
                        ))
                    
                    # Звук выстрела
                    self.sound_manager.play_sound("shoot")
    
    def spawn_enemies(self):
        if not self.wave_system.should_spawn_enemy():
            return
        
        now = pygame.time.get_ticks()
        difficulty = self.wave_system.get_difficulty()
        
        if now - self.last_enemy_spawn > self.spawn_rate / difficulty:
            self.last_enemy_spawn = now
            
            angle = random.uniform(0, math.tau)
            distance = random.uniform(800, 1200)
            spawn_pos = self.player.pos + pygame.Vector2(
                math.cos(angle) * distance,
                math.sin(angle) * distance
            )
            
            # Типы врагов зависят от волны или времени (endless)
            rand = random.random()
            
            if self.game_mode == GameMode.ENDLESS:
                # В бесконечном режиме используем время
                time_elapsed = self.time_survived
                
                if time_elapsed < 60:  # Первая минута
                    enemy_type = "basic"
                elif time_elapsed < 120:  # 1-2 минуты
                    enemy_type = random.choices(["basic", "fast", "swarm"], weights=[55, 30, 15])[0]
                elif time_elapsed < 180:  # 2-3 минуты
                    enemy_type = random.choices(["basic", "fast", "tank", "swarm", "sniper", "ranger", "lancer"], weights=[25, 25, 15, 15, 8, 7, 5])[0]
                elif time_elapsed < 300:  # 3-5 минут
                    enemy_type = random.choices(["basic", "fast", "tank", "swarm", "sniper", "ghost", "ranger", "healer"], weights=[20, 22, 18, 12, 10, 8, 6, 4])[0]
                elif time_elapsed < 480:  # 5-8 минут
                    enemy_type = random.choices(["basic", "fast", "tank", "swarm", "sniper", "ghost", "bruiser", "lancer", "buffer"], weights=[12, 18, 18, 12, 10, 10, 10, 6, 4])[0]
                else:  # После 8 минут
                    enemy_type = random.choices(["basic", "fast", "tank", "sniper", "ghost", "bruiser", "leech", "bomber", "sentinel", "boss", "ranger", "mortar", "shielder", "lancer", "healer", "buffer"], weights=[6, 9, 10, 7, 7, 9, 5, 5, 5, 6, 5, 4, 6, 5, 4, 7])[0]
            else:
                # Режим волн
                wave_num = self.wave_system.current_wave
                
                if wave_num <= 2:
                    enemy_type = random.choices(["basic", "swarm"], weights=[80, 20])[0]
                elif wave_num <= 4:
                    enemy_type = random.choices(["basic", "fast", "swarm"], weights=[55, 30, 15])[0]
                elif wave_num <= 7:
                    enemy_type = random.choices(["basic", "fast", "tank", "swarm", "sniper", "ranger", "lancer"], weights=[25, 25, 15, 15, 8, 7, 5])[0]
                elif wave_num <= 12:
                    enemy_type = random.choices(["basic", "fast", "tank", "sniper", "ghost", "swarm", "ranger", "mortar", "lancer", "healer"], weights=[15, 20, 15, 10, 10, 8, 8, 5, 5, 4])[0]
                else:
                    enemy_type = random.choices(["basic", "fast", "tank", "sniper", "ghost", "bruiser", "leech", "bomber", "sentinel", "boss", "ranger", "mortar", "shielder", "lancer", "healer", "buffer"], weights=[6, 9, 10, 7, 7, 9, 5, 5, 5, 7, 5, 4, 7, 5, 4, 5])[0]
            
            new_enemy = Enemy(spawn_pos, enemy_type, difficulty)
            # Мини-босс каждые 5 волн (1 на волну, не быстрые типы)
            wave_num = self.wave_system.current_wave
            if (self.game_mode == GameMode.WAVES and 
                    wave_num % 5 == 0 and wave_num > 0 and
                    enemy_type not in ("fast", "swarm") and
                    not getattr(self, '_miniboss_spawned_this_wave', False) and
                    self.wave_system.wave_active and
                    self.wave_system.enemies_spawned == 1):
                # Превращаем в мини-босса (усиленного)
                new_enemy.is_miniboss = True
                new_enemy.max_hp = int(new_enemy.max_hp * 5.0)   # было 3.5
                new_enemy.hp = new_enemy.max_hp
                new_enemy.dmg = int(new_enemy.dmg * 2.5)          # было 2
                new_enemy.speed = max(1.5, new_enemy.speed * 0.8)
                new_enemy.size = int(new_enemy.size * 1.8)        # было 1.6
                new_enemy.exp_value = int(new_enemy.exp_value * 5)
                # Золотой оттенок
                base = new_enemy.color
                new_enemy.color = (
                    min(255, int(base[0] * 0.5 + 255 * 0.5)),
                    min(255, int(base[1] * 0.5 + 215 * 0.5)),
                    min(255, int(base[2] * 0.2)),
                )
                # Броня мини-босса
                new_enemy.damage_reduction = getattr(new_enemy, 'damage_reduction', 0) + 0.15
                self._miniboss_spawned_this_wave = True
            self.enemies.append(new_enemy)
            self.wave_system.enemy_spawned()
    
    def update_combat(self):
        # Пули попадают во врагов (оптимизация: проверяем квадрат расстояния)
        for bullet in self.bullets[:]:
            hit_count = 0
            bullet_pos = bullet.pos
            collision_dist_sq = (bullet.size * 4) ** 2  # Квадрат расстояния
            
            for enemy in self.enemies[:]:
                # Оптимизация: сначала проверяем квадрат расстояния (без sqrt)
                dx = bullet_pos.x - enemy.pos.x
                dy = bullet_pos.y - enemy.pos.y
                dist_sq = dx * dx + dy * dy
                required_dist_sq = (enemy.size + bullet.size * 4) ** 2
                
                if dist_sq < required_dist_sq:
                    if enemy.take_damage(bullet.dmg):
                        self.particle_system.emit(enemy.pos, 15, enemy.color)
                        self.exp_gems.append(pygame.Vector2(enemy.pos))
                        if enemy in self.enemies:
                            self.enemies.remove(enemy)
                        self.kills += 1
                        self.score += enemy.exp_value
                        
                        # Звук смерти врага (не каждый раз для оптимизации)
                        if random.random() < 0.3:  # 30% шанс звука
                            self.sound_manager.play_sound("enemy_death")
                        
                        # Вампиризм
                        if self.player.lifesteal > 0:
                            heal = int(bullet.dmg * self.player.lifesteal)
                            self.player.heal(heal)
                    else:
                        # Звук попадания (не каждый раз)
                        if random.random() < 0.2:  # 20% шанс звука
                            self.sound_manager.play_sound("enemy_hit")
                        
                        # ====== ПРИМЕНЕНИЕ ЭФФЕКТОВ ======
                        # Замедляющие пули
                        if hasattr(self.player, 'slow_bullets') and self.player.slow_bullets:
                            enemy.slow_duration = max(enemy.slow_duration, 2000)
                            enemy.slow_factor = min(enemy.slow_factor, 0.6)
                        
                        # Яд
                        if hasattr(self.player, 'poison_bullets') and self.player.poison_bullets:
                            enemy.poison_damage = 15  # урон в секунду (увеличено с 5)
                            enemy.poison_duration = 3000  # миллисекунды
                        
                        # Заморозка
                        if hasattr(self.player, 'freeze_bullets') and self.player.freeze_bullets:
                            enemy.frozen_duration = 2000  # миллисекунды
                        
                        # Цепная молния
                        if hasattr(self.player, 'chain_lightning') and self.player.chain_lightning > 0:
                            chain_targets = []
                            for other in self.enemies:
                                if other != enemy and (other.pos - enemy.pos).length() < 300:
                                    chain_targets.append(other)
                            
                            chain_targets.sort(key=lambda e: (e.pos - enemy.pos).length())
                            for i, target in enumerate(chain_targets[:self.player.chain_lightning]):
                                chain_dmg = int(bullet.dmg * 0.6)
                                target.chain_lightning_target = True
                                target.chain_lightning_timer = 500
                                if target.take_damage(chain_dmg):
                                    if target in self.enemies:
                                        self.particle_system.emit(target.pos, 12, (255, 255, 100))
                                        self.exp_gems.append(pygame.Vector2(target.pos))
                                        self.enemies.remove(target)
                                        self.kills += 1
                                        self.score += target.exp_value
                        
                        # Взрыв - немедленно при попадании, AOE урон
                        if hasattr(self.player, 'explosive_bullets') and self.player.explosive_bullets:
                            exp_dmg = max(6, int(bullet.dmg * 0.6))
                            exp_radius = 90
                            self.particle_system.emit(enemy.pos, 25, (255, 160, 40), (3, 12))
                            for other in self.enemies[:]:
                                if other != enemy and (other.pos - enemy.pos).length() < exp_radius:
                                    if other.take_damage(exp_dmg) and other in self.enemies:
                                        self.particle_system.emit(other.pos, 8, (255, 100, 20))
                                        self.exp_gems.append(pygame.Vector2(other.pos))
                                        self.enemies.remove(other)
                                        self.kills += 1
                                        self.score += other.exp_value
                            self.sound_manager.play_sound("explosion")
                    
                    hit_count += 1
                    if hit_count > bullet.piercing:
                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                        break
        
        # Враги атакуют игрока (оптимизация)
        player_pos = self.player.pos
        player_size = self.player.size
        
        # Орбитальные пули наносят урон врагам
        if hasattr(self.player, 'orbital_bullets') and self.player.orbital_bullets > 0:
            time_ms = pygame.time.get_ticks()
            orbit_radius = 55
            if not hasattr(self, '_orbital_hit_times'):
                self._orbital_hit_times = {}
            for i in range(self.player.orbital_bullets):
                angle = (time_ms / 1000 + i * (6.28 / self.player.orbital_bullets)) % 6.28
                orb_pos = pygame.Vector2(
                    player_pos.x + math.cos(angle) * orbit_radius,
                    player_pos.y + math.sin(angle) * orbit_radius
                )
                for enemy in self.enemies[:]:
                    if (enemy.pos - orb_pos).length() < enemy.size + 10:
                        eid = id(enemy)
                        last_hit = self._orbital_hit_times.get(eid, 0)
                        if time_ms - last_hit > 400:  # Каждые 400мс
                            self._orbital_hit_times[eid] = time_ms
                            orb_dmg = max(5, int(self.player.dmg * 0.5))
                            if enemy.take_damage(orb_dmg):
                                self.particle_system.emit(enemy.pos, 10, enemy.color)
                                self.exp_gems.append(pygame.Vector2(enemy.pos))
                                if enemy in self.enemies:
                                    self.enemies.remove(enemy)
                                self.kills += 1
                                self.score += enemy.exp_value
                                self._orbital_hit_times.pop(eid, None)
        
        for enemy in self.enemies[:]:
            dx = enemy.pos.x - player_pos.x
            dy = enemy.pos.y - player_pos.y
            dist_sq = dx * dx + dy * dy
            required_dist_sq = (enemy.size + player_size) ** 2
            
            if dist_sq < required_dist_sq:
                if self.player.take_damage(enemy.dmg):
                    self.state = GameState.GAME_OVER
                    # Статистика учитывается только в режиме волн
                    count_stats = (self.game_mode == GameMode.WAVES)
                    earned = self.save_system.update_stats(
                        self.kills,
                        int(self.time_survived),
                        self.score,
                        self.player.level,
                        self.wave_system.current_wave,
                        count_stats
                    )
                    # Проверка достижений
                    AchievementSystem.check_achievements(self, self.save_system)
                else:
                    # Звук получения урона
                    self.sound_manager.play_sound("player_hit")
                    # Пиявка лечится при атаке игрока
                    if getattr(enemy, 'leech_heal', 0) > 0:
                        enemy.hp = min(enemy.max_hp, enemy.hp + enemy.leech_heal)
                    
                    # Шипы - урон врагу при касании
                    thorns_dmg = getattr(self.player, 'thorns_damage', 0) + self.player.thorns
                    if thorns_dmg > 0:
                        if enemy.take_damage(int(thorns_dmg)):
                            self.particle_system.emit(enemy.pos, 15, enemy.color)
                            self.exp_gems.append(pygame.Vector2(enemy.pos))
                            if enemy in self.enemies:
                                self.enemies.remove(enemy)
                            self.kills += 1
                            self.score += enemy.exp_value
                    
                    # Отражение урона
                    if hasattr(self.player, 'reflect_damage') and self.player.reflect_damage > 0:
                        reflected = int(enemy.dmg * self.player.reflect_damage)
                        if enemy.take_damage(reflected):
                            self.particle_system.emit(enemy.pos, 15, enemy.color)
                            self.exp_gems.append(pygame.Vector2(enemy.pos))
                            if enemy in self.enemies:
                                self.enemies.remove(enemy)
                            self.kills += 1
                            self.score += enemy.exp_value
                
                self.particle_system.emit(self.player.pos, 10, COLORS["health"])
        
        # ---- Обновление снарядов врагов ----
        if not hasattr(self, 'enemy_bullets'):
            self.enemy_bullets = []
        now_ms = pygame.time.get_ticks()
        
        # Стрельба дальнобойных врагов
        for enemy in self.enemies:
            if enemy.type == "ranger":
                if getattr(enemy, 'shoot_cooldown', 0) <= 0:
                    d = self.player.pos - enemy.pos
                    if d.length() < 600:
                        shots = 3 if getattr(enemy, 'triple_shot', False) else 1
                        # Slight lead on player
                        bullet_spd = 5
                        travel_time = d.length() / (bullet_spd * 60)
                        predicted = self.player.pos + self.player.velocity * travel_time * 60 * 0.35
                        aim_dir = predicted - enemy.pos
                        if aim_dir.length() == 0:
                            aim_dir = d
                        for si in range(shots):
                            angle_off = (si - shots // 2) * 12
                            spd_vec = pygame.Vector2(aim_dir).normalize().rotate(angle_off) * bullet_spd
                            self.enemy_bullets.append({
                                'pos': pygame.Vector2(enemy.pos), 'vel': spd_vec,
                                'dmg': enemy.dmg, 'birth': now_ms, 'lifetime': 2500,
                                'color': enemy.color, 'size': 7, 'type': 'ranger'
                            })
                    enemy.shoot_cooldown = enemy.shoot_interval
            elif enemy.type == "sniper":
                if getattr(enemy, 'shoot_cooldown', 0) <= 0:
                    d = self.player.pos - enemy.pos
                    if d.length() < 700:
                        # Упреждение: предсказываем позицию игрока
                        bullet_speed_val = 8
                        travel_time = d.length() / (bullet_speed_val * 60)
                        predicted_pos = self.player.pos + self.player.velocity * travel_time * 60 * 0.6
                        aim_dir = predicted_pos - enemy.pos
                        if aim_dir.length() > 0:
                            spd_vec = aim_dir.normalize() * bullet_speed_val
                        else:
                            spd_vec = pygame.Vector2(d).normalize() * bullet_speed_val
                        self.enemy_bullets.append({
                            'pos': pygame.Vector2(enemy.pos), 'vel': spd_vec,
                            'dmg': enemy.dmg, 'birth': now_ms, 'lifetime': 2000,
                            'color': enemy.color, 'size': 8, 'type': 'sniper',
                            'armor_pierce': getattr(enemy, 'armor_pierce', False)
                        })
                    enemy.shoot_cooldown = enemy.shoot_interval
            elif enemy.type == "lancer":
                if getattr(enemy, 'shoot_cooldown', 0) <= 0:
                    d = self.player.pos - enemy.pos
                    if d.length() < 600:
                        spd_vec = pygame.Vector2(d).normalize() * 6
                        self.enemy_bullets.append({
                            'pos': pygame.Vector2(enemy.pos), 'vel': spd_vec,
                            'dmg': enemy.dmg, 'birth': now_ms, 'lifetime': 2000,
                            'color': enemy.color, 'size': 6, 'type': 'lancer',
                            'piercing': True
                        })
                    enemy.shoot_cooldown = enemy.shoot_interval
            elif enemy.type == "mortar":
                if getattr(enemy, 'shoot_cooldown', 0) <= 0:
                    d = self.player.pos - enemy.pos
                    if d.length() < 700:
                        # Мортира стреляет слегка заупреждённо
                        spd = pygame.Vector2(d).normalize() * 3.5
                        self.enemy_bullets.append({
                            'pos': pygame.Vector2(enemy.pos), 'vel': spd,
                            'dmg': enemy.dmg, 'birth': now_ms, 'lifetime': 2000,
                            'color': (255, 140, 0), 'size': 12, 'type': 'mortar',
                            'target': pygame.Vector2(self.player.pos)
                        })
                    enemy.shoot_cooldown = enemy.shoot_interval
            elif enemy.type == "shielder":
                # Наделяет временным щитом ближних врагов
                if getattr(enemy, 'aura_timer', 0) <= 0:
                    enemy.aura_timer = 1500  # каждые 1.5 сек
                    aura_r = getattr(enemy, 'aura_radius', 200)
                    for ally in self.enemies:
                        if ally is not enemy and ally.type != "shielder":
                            if (ally.pos - enemy.pos).length() < aura_r:
                                # Мини-щит: уменьшает следующий урон
                                ally.shield_buff = min(getattr(ally, 'shield_buff', 0) + 25, 100)
            elif enemy.type == "healer":
                # Лечит союзников вокруг
                if getattr(enemy, 'heal_timer', 0) <= 0:
                    enemy.heal_timer = enemy.heal_interval
                    heal_r = getattr(enemy, 'heal_radius', 200)
                    for ally in self.enemies:
                        if ally is not enemy:
                            if (ally.pos - enemy.pos).length() < heal_r:
                                ally.hp = min(ally.max_hp, ally.hp + enemy.heal_amount)
            elif enemy.type == "buffer":
                # Даёт союзникам ускорение и бонус урона
                if getattr(enemy, 'buff_timer', 0) <= 0:
                    enemy.buff_timer = enemy.buff_interval
                    buff_r = getattr(enemy, 'buff_radius', 180)
                    for ally in self.enemies:
                        if ally is not enemy:
                            if (ally.pos - enemy.pos).length() < buff_r:
                                ally.speed_buff_timer = 2000
                                # Временно увеличиваем скорость
                                if not hasattr(ally, '_base_speed_saved'):
                                    ally._base_speed_saved = ally.speed
                                ally.speed = ally._base_speed_saved * 1.4
        
        # Обновление и проверка попаданий снарядов врагов
        for eb in self.enemy_bullets[:]:
            eb['pos'] += eb['vel']
            age = now_ms - eb['birth']
            if age > eb['lifetime']:
                self.enemy_bullets.remove(eb)
                # Мортира: взрыв при истечении времени в целевой точке
                if eb['type'] == 'mortar':
                    target = eb.get('target', eb['pos'])
                    exp_r = 120
                    self.particle_system.emit(target, 30, (255, 140, 0), (3, 10))
                    if (self.player.pos - target).length() < exp_r:
                        if self.player.take_damage(eb['dmg']):
                            self.state = GameState.GAME_OVER
                continue
            # Обычное попадание в игрока
            dp = self.player.pos - eb['pos']
            if dp.length() < self.player.size + eb['size']:
                if eb['type'] != 'mortar':  # Мортира взрывается по таймеру
                    # Снайпер пробивает неуязвимость
                    if eb.get('armor_pierce') and self.player.invulnerable > 0:
                        self.player.hp -= eb['dmg']
                        self.player.hit_flash = 200
                        if self.player.hp <= 0:
                            self.state = GameState.GAME_OVER
                    elif self.player.take_damage(eb['dmg']):
                        self.state = GameState.GAME_OVER
                    else:
                        self.particle_system.emit(self.player.pos, 6, eb['color'])
                    self.enemy_bullets.remove(eb)
    
    def update_exp_gems(self):
        """Обновление и притяжение кристаллов опыта"""
        magnet_radius = getattr(self.player, 'exp_magnet_radius', 100)
        for gem in self.exp_gems[:]:
            to_player = self.player.pos - gem
            if to_player.length() < magnet_radius:
                pull_speed = 8 + (1 - to_player.length() / magnet_radius) * 12
                gem += to_player.normalize() * pull_speed
            if to_player.length() < 20:
                self.exp_gems.remove(gem)
                exp_gain = 10
                if hasattr(self.player, 'exp_multiplier'):
                    exp_gain = int(exp_gain * self.player.exp_multiplier)
                self.player.exp += exp_gain
                if self.player.exp >= self.player.exp_to_next:
                    self.player.level += 1
                    self.player.exp = 0
                    self.player.exp_to_next = int(self.player.exp_to_next * 1.2)
                    self.state = GameState.LEVEL_UP
                    self.level_up_click_handled = True
                    self.sound_manager.play_sound("level_up")

    def update_wave_system(self):
        # Проверяем окончание волны
        if self.wave_system.wave_active:
            if (self.wave_system.enemies_spawned >= self.wave_system.enemies_in_wave 
                and len(self.enemies) == 0):
                self.wave_system.wave_complete()
                self.state = GameState.WAVE_COMPLETE
        
        # Обновляем перерыв
        if not self.wave_system.wave_active:
            if self.wave_system.update_break(self.dt):
                self._miniboss_spawned_this_wave = False
                self.wave_system.start_wave()
    
    def draw_background(self):
        # Dark base fill
        screen.fill((8, 10, 20))
        
        time_ms = pygame.time.get_ticks()
        
        # Grid spacing in world units
        GRID = 80
        # Camera offset (how much world has scrolled)
        off_x = int(self.cam.x) % GRID
        off_y = int(self.cam.y) % GRID
        
        line_col = (18, 22, 38)
        # Vertical lines
        for x in range(-GRID + off_x, WIDTH + GRID, GRID):
            pygame.draw.line(screen, line_col, (x, 0), (x, HEIGHT), 1)
        # Horizontal lines
        for y in range(-GRID + off_y, HEIGHT + GRID, GRID):
            pygame.draw.line(screen, line_col, (0, y), (WIDTH, y), 1)
        
        # Dots at every grid intersection
        dot_col = (32, 40, 65)
        for x in range(-GRID + off_x, WIDTH + GRID, GRID):
            for y in range(-GRID + off_y, HEIGHT + GRID, GRID):
                pygame.draw.circle(screen, dot_col, (x, y), 2)
        
        # Every 4th intersection: glowing accent dot
        GRID4 = GRID * 4
        off4_x = int(self.cam.x) % GRID4
        off4_y = int(self.cam.y) % GRID4
        pulse = abs(math.sin(time_ms / 1800)) * 0.5 + 0.5
        accent = (int(20 + 30 * pulse), int(35 + 50 * pulse), int(70 + 80 * pulse))
        for x in range(-GRID4 + off4_x, WIDTH + GRID4, GRID4):
            for y in range(-GRID4 + off4_y, HEIGHT + GRID4, GRID4):
                if 0 <= x <= WIDTH and 0 <= y <= HEIGHT:
                    pygame.draw.circle(screen, accent, (x, y), 3)
    
    def draw_ui(self):
        margin = 30
        
        # HP бар с улучшенным дизайном
        bar_w, bar_h = 380, 35
        bar_x, bar_y = margin, margin
        
        # Подложка с тенью
        shadow_rect = pygame.Rect(bar_x + 2, bar_y + 2, bar_w, bar_h)
        pygame.draw.rect(screen, (0, 0, 0, 60), shadow_rect, border_radius=8)
        
        # Фон бара
        pygame.draw.rect(screen, (25, 30, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=8)
        
        # HP заполнение с градиентом
        hp_w = int((self.player.hp / self.player.max_hp) * bar_w)
        if hp_w > 0:
            hp_rect = pygame.Rect(bar_x, bar_y, hp_w, bar_h)
            # Градиент от темно-красного к яркому
            for i in range(hp_w):
                progress = i / bar_w
                r = int(200 + (255 - 200) * progress)
                g = int(60 + (80 - 60) * progress)
                b = int(60 + (80 - 60) * progress)
                pygame.draw.line(screen, (r, g, b), 
                               (bar_x + i, bar_y + 2), 
                               (bar_x + i, bar_y + bar_h - 2))
            pygame.draw.rect(screen, COLORS["health"], (bar_x, bar_y, hp_w, bar_h), 3, border_radius=8)
        
        # Обводка
        pygame.draw.rect(screen, COLORS["card_border"], (bar_x, bar_y, bar_w, bar_h), 2, border_radius=8)
        
        # Текст HP
        hp_text = self.font_small.render(f"HP: {int(self.player.hp)} / {self.player.max_hp}", 
                                         True, COLORS["ui"])
        screen.blit(hp_text, (bar_x + bar_w // 2 - hp_text.get_width() // 2, bar_y + 7))
        
        current_y = bar_y + bar_h + 10
        
        # Щит (если есть)
        if self.player.max_shield > 0:
            shield_h = 25
            pygame.draw.rect(screen, (20, 25, 35), (bar_x, current_y, bar_w, shield_h), border_radius=6)
            shield_w = int((self.player.shield / self.player.max_shield) * bar_w)
            if shield_w > 0:
                pygame.draw.rect(screen, COLORS["shield"], (bar_x, current_y, shield_w, shield_h), border_radius=6)
            pygame.draw.rect(screen, COLORS["card_border"], (bar_x, current_y, bar_w, shield_h), 2, border_radius=6)
            current_y += shield_h + 8
        
        # EXP бар с улучшенным дизайном
        exp_h = 30
        pygame.draw.rect(screen, (20, 25, 35), (bar_x, current_y, bar_w, exp_h), border_radius=7)
        exp_w = int((self.player.exp / self.player.exp_to_next) * bar_w)
        if exp_w > 0:
            # Градиент для опыта
            for i in range(exp_w):
                progress = i / bar_w
                r = int(0 + (0 - 0) * progress)
                g = int(180 + (220 - 180) * progress)
                b = int(230 + (255 - 230) * progress)
                pygame.draw.line(screen, (r, g, b), 
                               (bar_x + i, current_y + 2), 
                               (bar_x + i, current_y + exp_h - 2))
            pygame.draw.rect(screen, COLORS["exp"], (bar_x, current_y, exp_w, exp_h), 3, border_radius=7)
        
        pygame.draw.rect(screen, COLORS["card_border"], (bar_x, current_y, bar_w, exp_h), 2, border_radius=7)
        
        # Процентный индикатор опыта
        exp_percent = int((self.player.exp / self.player.exp_to_next) * 100)
        exp_text = self.font_small.render(f"EXP: {exp_percent}%", True, COLORS["ui"])
        screen.blit(exp_text, (bar_x + bar_w // 2 - exp_text.get_width() // 2, current_y + 5))
        
        # Уровень справа от бара
        lvl_text = self.font_medium.render(f"LVL {self.player.level}", True, COLORS["player"])
        screen.blit(lvl_text, (bar_x + bar_w + 20, current_y - 5))
        
        current_y += exp_h + 12
        
        # Компактные статы — два ряда при необходимости
        time_str = f"{int(self.time_survived // 60)}м{int(self.time_survived % 60)}с" if self.time_survived >= 60 else f"{int(self.time_survived)}с"
        
        if self.game_mode == GameMode.WAVES:
            line1 = f"СЧЁТ: {self.score}  |  УБИЙСТВ: {self.kills}"
            line2 = f"ВОЛНА: {self.wave_system.current_wave}  |  ВРЕМЯ: {time_str}"
        else:
            line1 = f"СЧЁТ: {self.score}  |  УБИЙСТВ: {self.kills}"
            line2 = f"ВРЕМЯ: {time_str}  |  ВРАГИ: {len(self.enemies)}"
        
        stat_h = 50
        stat_bg = pygame.Rect(bar_x, current_y, bar_w, stat_h)
        pygame.draw.rect(screen, (25, 30, 45), stat_bg, border_radius=6)
        pygame.draw.rect(screen, COLORS["card_border"], stat_bg, 1, border_radius=6)
        stats_text1 = self.font_tiny.render(line1, True, (180, 180, 200))
        stats_text2 = self.font_tiny.render(line2, True, (180, 180, 200))
        screen.blit(stats_text1, (bar_x + bar_w//2 - stats_text1.get_width()//2, current_y + 6))
        screen.blit(stats_text2, (bar_x + bar_w//2 - stats_text2.get_width()//2, current_y + 27))
        
        current_y += stat_h + 5
        
        # Единый виджет волны/режима в центре сверху
        wave_bg = pygame.Rect(WIDTH // 2 - 220, 20, 440, 46)
        pygame.draw.rect(screen, (28, 32, 50), wave_bg, border_radius=10)
        
        if self.game_mode == GameMode.WAVES:
            if not self.wave_system.wave_active:
                pygame.draw.rect(screen, COLORS["warning"], wave_bg, 2, border_radius=10)
                wt = self.font_small.render(
                    f"Волна {self.wave_system.current_wave} | Перерыв: {int(self.wave_system.wave_break_time)}с",
                    True, COLORS["warning"])
            else:
                remaining = max(0, (self.wave_system.enemies_in_wave - self.wave_system.enemies_spawned) + len(self.enemies))
                pygame.draw.rect(screen, COLORS["player"], wave_bg, 2, border_radius=10)
                wt = self.font_small.render(
                    f"Волна {self.wave_system.current_wave}  |  Врагов: {remaining}",
                    True, COLORS["ui"])
        else:
            pygame.draw.rect(screen, COLORS["exp"], wave_bg, 2, border_radius=10)
            wt = self.font_small.render(f"БЕСКОНЕЧНЫЙ  |  Врагов: {len(self.enemies)}", True, COLORS["exp"])
        
        screen.blit(wt, wt.get_rect(center=wave_bg.center))
        
        # Dash индикатор в красивом стиле
        dash_w = 180
        dash_h = 50
        dash_x = WIDTH // 2 - dash_w // 2
        dash_y = HEIGHT - 70
        
        dash_bg = pygame.Rect(dash_x, dash_y, dash_w, dash_h)
        
        if self.player.dash_ready:
            pygame.draw.rect(screen, (40, 50, 65), dash_bg, border_radius=10)
            pygame.draw.rect(screen, COLORS["player"], dash_bg, 3, border_radius=10)
            dash_text = self.font_small.render("DASH ГОТОВ", True, COLORS["player"])
        else:
            pygame.draw.rect(screen, (30, 35, 45), dash_bg, border_radius=10)
            pygame.draw.rect(screen, (80, 80, 90), dash_bg, 2, border_radius=10)
            cooldown = max(0, self.player.dash_cooldown / 1000)
            dash_text = self.font_small.render(f"DASH: {cooldown:.1f}s", True, (120, 120, 130))
        
        dash_rect = dash_text.get_rect(center=dash_bg.center)
        screen.blit(dash_text, dash_rect)
        
        # Active ability HUD
        active_ab = self.save_system.data.get("active_ability", "")
        AB_NAMES = {"dash_boost":"РЫВОК-УДАР","shield_pulse":"ИМПУЛЬС ЩИТА","time_slow":"ЗАМЕДЛЕНИЕ",
                    "overdrive":"ПЕРЕГРУЗКА","nuke":"ЯДЕРНЫЙ ЗАРЯД","heal_pulse":"ПУЛЬС ИСЦЕЛЕНИЯ",
                    "bullet_storm":"ШТОРМ ПУЛЬ"}
        AB_COLORS = {"dash_boost":COLORS["player"],"shield_pulse":COLORS["shield"],"time_slow":(100,200,255),
                     "overdrive":COLORS["warning"],"nuke":COLORS["enemy"],"heal_pulse":(100,255,150),
                     "bullet_storm":(255,180,50)}
        if active_ab and active_ab in AB_NAMES:
            ab_w, ab_h = 160, 50
            ab_x = WIDTH // 2 + 110
            ab_bg = pygame.Rect(ab_x, HEIGHT - 70, ab_w, ab_h)
            ab_col = AB_COLORS.get(active_ab, COLORS["player"])
            if self.ability_cooldown <= 0:
                pygame.draw.rect(screen, (35, 45, 60), ab_bg, border_radius=10)
                pygame.draw.rect(screen, ab_col, ab_bg, 2, border_radius=10)
                at = self.font_tiny.render(AB_NAMES[active_ab], True, ab_col)
            else:
                pygame.draw.rect(screen, (25, 30, 42), ab_bg, border_radius=10)
                pygame.draw.rect(screen, (70, 70, 85), ab_bg, 2, border_radius=10)
                cd_sec = self.ability_cooldown / 1000
                at = self.font_tiny.render(f"КД: {cd_sec:.1f}s", True, (130,130,145))
                # Cooldown fill bar
                ab_kd_map = {"dash_boost":0,"shield_pulse":6000,"time_slow":12000,"overdrive":15000,"nuke":20000,
                             "heal_pulse":18000,"bullet_storm":10000}
                max_cd = ab_kd_map.get(active_ab, 10000)
                if max_cd > 0:
                    fill_w = int((1 - self.ability_cooldown / max_cd) * (ab_w - 8))
                    if fill_w > 0:
                        pygame.draw.rect(screen, (40, 50, 65), (ab_bg.x + 4, ab_bg.y + ab_h - 10, ab_w - 8, 6), border_radius=3)
                        pygame.draw.rect(screen, ab_col, (ab_bg.x + 4, ab_bg.y + ab_h - 10, fill_w, 6), border_radius=3)
            screen.blit(at, at.get_rect(center=(ab_bg.centerx, ab_bg.centery - 3)))
        
    def draw_menu(self):
        screen.fill(COLORS["bg"])
        
        if self.menu_page == "main":
            self.draw_main_menu()
        elif self.menu_page == "stats":
            self.draw_stats_menu()
        elif self.menu_page == "settings":
            self.draw_settings_menu()
        elif self.menu_page == "shop" or self.menu_page == "modules":
            self.draw_modules_menu()
        elif self.menu_page == "skins":
            self.draw_skins_menu()
        elif self.menu_page == "achievements":
            self.draw_achievements_menu()
        elif self.menu_page == "knowledge":
            self.draw_knowledge_menu()
    
    def draw_main_menu(self):
        # Улучшенный градиентный фон с более плавными переходами
        for i in range(HEIGHT):
            progress = i / HEIGHT
            # Более темный и атмосферный градиент
            r = int(5 + (15 - 5) * progress)
            g = int(8 + (20 - 8) * progress)
            b = int(18 + (35 - 18) * progress)
            pygame.draw.line(screen, (r, g, b), (0, i), (WIDTH, i))
        
        # Анимированные декоративные линии
        time_offset = pygame.time.get_ticks() // 50
        for i in range(30):
            x = (WIDTH // 30) * i + (time_offset % 100)
            alpha = 8 + (i % 4) * 4
            y_wave = int(math.sin((i + time_offset / 100) * 0.5) * 20)
            color = (*COLORS["grid"], alpha)
            s = pygame.Surface((2, HEIGHT), pygame.SRCALPHA)
            s.fill(color)
            screen.blit(s, (x, y_wave))
        
        # Плавающие частицы в фоне
        if len(self.menu_particles) < 50:
            self.menu_particles.append({
                'x': random.randint(0, WIDTH),
                'y': random.randint(0, HEIGHT),
                'speed': random.uniform(10, 30),
                'size': random.randint(2, 4),
                'alpha': random.randint(40, 100)
            })
        
        for particle in self.menu_particles[:]:
            particle['y'] -= particle['speed'] * self.dt
            if particle['y'] < -10:
                particle['y'] = HEIGHT + 10
                particle['x'] = random.randint(0, WIDTH)
            
            # Рисуем частицу
            surf = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*COLORS["player"], particle['alpha']), 
                             (particle['size'], particle['size']), particle['size'])
            screen.blit(surf, (int(particle['x']), int(particle['y'])))
        
        # Заголовок с усиленным эффектом свечения
        title = self.font_huge.render("CYBER SURVIVOR", True, COLORS["player"])
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 6))
        
        # Многослойное свечение заголовка
        glow_surf = pygame.Surface((title_rect.width + 60, title_rect.height + 60), pygame.SRCALPHA)
        for i in range(5):
            alpha = 40 - i * 8
            offset = i * 3
            glow_title = self.font_huge.render("CYBER SURVIVOR", True, (*COLORS["player_glow"], alpha))
            glow_surf.blit(glow_title, (30 + offset, 30 + offset))
        screen.blit(glow_surf, (title_rect.x - 30, title_rect.y - 30))
        screen.blit(title, title_rect)
        
        # Анимированный подзаголовок
        pulse = abs(math.sin(self.menu_time * 2)) * 30 + 200
        subtitle = self.font_small.render("v4.3 - Обновление интерфейса. Новые враги и способности", True, (int(pulse), int(pulse), 255))
        subtitle_rect = subtitle.get_rect(center=(WIDTH // 2, HEIGHT // 6 + 70))
        screen.blit(subtitle, subtitle_rect)
        
        # Карточки - сетка 2x4 с улучшенным дизайном
        card_width, card_height = 360, 100
        gap = 25
        grid_cols = 2
        
        start_x = WIDTH // 2 - (card_width * grid_cols + gap * (grid_cols - 1)) // 2
        start_y = HEIGHT // 2 - 120  # Немного поднято вверх
        
        buttons = [
            {"text": "НАЧАТЬ ИГРУ", "action": "play", "desc": "Новая игра", "id": "play", "icon": ">"},
            {"text": "МАГАЗИН", "action": "shop", "desc": "Модули и Способности", "id": "mod", "icon": "$"},
            {"text": "СКИНЫ", "action": "skins", "desc": "Внешний вид", "id": "skin", "icon": "#"},
            {"text": "БАЗА ЗНАНИЙ", "action": "knowledge", "desc": "Враги и Перки", "id": "know", "icon": "?"},
            {"text": "ДОСТИЖЕНИЯ", "action": "achievements", "desc": "Ваши награды", "id": "ach", "icon": "*"},
            {"text": "СТАТИСТИКА", "action": "stats", "desc": "Ваши рекорды", "id": "stat", "icon": "~"},
            {"text": "НАСТРОЙКИ", "action": "settings", "desc": "Конфигурация", "id": "set", "icon": "="},
            {"text": "ВЫХОД", "action": "quit", "desc": "Выйти из игры", "id": "quit", "icon": "X"}
        ]
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        
        for i, btn_data in enumerate(buttons):
            row = i // grid_cols
            col = i % grid_cols
            
            card_rect = pygame.Rect(
                start_x + col * (card_width + gap),
                start_y + row * (card_height + gap),
                card_width,
                card_height
            )
            
            is_hover = card_rect.collidepoint(mouse_pos)
            
            # Эффект нажатия
            btn_id = btn_data.get("id", str(i))
            press_time = self.button_press_effect.get(btn_id, 0)
            if press_time > 0:
                self.button_press_effect[btn_id] = max(0, press_time - self.dt)
                press_factor = press_time / 0.2
                card_rect = card_rect.inflate(-int(6 * press_factor), -int(6 * press_factor))
            
            # Карточка с улучшенной тенью и свечением при наведении
            if is_hover:
                # Тень
                shadow_rect = card_rect.copy()
                shadow_rect.y += 6
                shadow_surf = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(shadow_surf, (0, 0, 0, 60), shadow_surf.get_rect(), border_radius=15)
                screen.blit(shadow_surf, shadow_rect)
                
                # Свечение
                glow_rect = card_rect.inflate(8, 8)
                glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*COLORS["player"], 30), glow_surf.get_rect(), border_radius=17)
                screen.blit(glow_surf, glow_rect)
            
            # Основная карточка
            card_color = (50, 55, 75) if is_hover else (30, 35, 55)
            pygame.draw.rect(screen, card_color, card_rect, border_radius=15)
            title_color = COLORS["player"] if is_hover else COLORS["ui"]
            border_color = COLORS["player"] if is_hover else COLORS["card_border"]
            border_width = 3 if is_hover else 2
            pygame.draw.rect(screen, border_color, card_rect, border_width, border_radius=15)
            
            # Иконка слева (56x56 зона)
            icon_zone_w = 70
            icon_cx = card_rect.x + icon_zone_w // 2
            icon_cy = card_rect.centery  # точно по центру карточки
            
            if not self.draw_icon(btn_data["action"], icon_cx, icon_cy, 36):
                # Fallback на символ
                icon_text = self.font_medium.render(btn_data.get("icon", ">"), True, title_color)
                icon_rect = icon_text.get_rect(center=(icon_cx, icon_cy))
                screen.blit(icon_text, icon_rect)
            
            # Разделитель иконки
            sep_x = card_rect.x + icon_zone_w
            pygame.draw.line(screen, border_color,
                             (sep_x, card_rect.y + 15),
                             (sep_x, card_rect.bottom - 15), 1)
            
            # Текст названия и описания справа от иконки
            text_x = sep_x + 18
            button_text = self.font_medium.render(btn_data["text"], True, title_color)
            screen.blit(button_text, (text_x, card_rect.centery - button_text.get_height() - 2))
            
            desc_text = self.font_tiny.render(btn_data["desc"], True, (150, 155, 175))
            screen.blit(desc_text, (text_x, card_rect.centery + 4))
            
            if is_hover and mouse_clicked:
                self.button_press_effect[btn_id] = 0.2  # Запускаем эффект нажатия
                # Звук клика
                self.sound_manager.play_sound("button_click")
                
                if btn_data["action"] == "play":
                    self.state = GameState.MODE_SELECT  # Переходим к выбору режима
                elif btn_data["action"] == "achievements":
                    self.menu_page = "achievements"
                elif btn_data["action"] == "shop":
                    self.menu_page = "shop"
                elif btn_data["action"] == "skins":
                    self.menu_page = "skins"
                elif btn_data["action"] == "settings":
                    self.menu_page = "settings"
                elif btn_data["action"] == "stats":
                    self.menu_page = "stats"
                elif btn_data["action"] == "knowledge":
                    self.menu_page = "knowledge"
                elif btn_data["action"] == "quit":
                    pygame.quit()
                    sys.exit()
                pygame.time.delay(200)
        
        # Валюта (показывается в магазине)
    
    def draw_mode_select(self):
        """Экран выбора режима игры"""
        # Тот же красивый фон что и в главном меню
        for i in range(HEIGHT):
            progress = i / HEIGHT
            r = int(5 + (15 - 5) * progress)
            g = int(8 + (20 - 8) * progress)
            b = int(18 + (35 - 18) * progress)
            pygame.draw.line(screen, (r, g, b), (0, i), (WIDTH, i))
        
        # Заголовок
        title = self.font_huge.render("ВЫБОР РЕЖИМА", True, COLORS["player"])
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        
        # Свечение заголовка
        glow_surf = pygame.Surface((title_rect.width + 60, title_rect.height + 60), pygame.SRCALPHA)
        for i in range(5):
            alpha = 40 - i * 8
            offset = i * 3
            glow_title = self.font_huge.render("ВЫБОР РЕЖИМА", True, (*COLORS["player_glow"], alpha))
            glow_surf.blit(glow_title, (30 + offset, 30 + offset))
        screen.blit(glow_surf, (title_rect.x - 30, title_rect.y - 30))
        screen.blit(title, title_rect)
        
        # Две большие карточки режимов (увеличены)
        card_width = 520
        card_height = 380
        gap = 70
        start_x = WIDTH // 2 - (card_width * 2 + gap) // 2
        card_y = HEIGHT // 2 - card_height // 2 + 30
        
        modes = [
            {
                "title": "ВОЛНЫ",
                "mode": GameMode.WAVES,
                "icon": "~",
                "desc": "Классический режим",
                "features": [
                    "Волны врагов с перерывами",
                    "Растущая сложность",
                    "Учитывается в статистике",
                    "Разблокировка достижений"
                ]
            },
            {
                "title": "БЕСКОНЕЧНЫЙ",
                "mode": GameMode.ENDLESS,
                "icon": "8",
                "desc": "Режим выживания",
                "features": [
                    "Постоянный спавн врагов",
                    "Без перерывов между волнами",
                    "Не учитывается в статистике",
                    "Только для практики"
                ]
            }
        ]
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        
        for i, mode_data in enumerate(modes):
            card_x = start_x + i * (card_width + gap)
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            
            is_hover = card_rect.collidepoint(mouse_pos)
            
            # Эффекты при наведении
            if is_hover:
                # Тень
                shadow_rect = card_rect.copy()
                shadow_rect.y += 8
                shadow_surf = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(shadow_surf, (0, 0, 0, 80), shadow_surf.get_rect(), border_radius=20)
                screen.blit(shadow_surf, shadow_rect)
                
                # Свечение
                glow_rect = card_rect.inflate(12, 12)
                glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*COLORS["player"], 40), glow_surf.get_rect(), border_radius=22)
                screen.blit(glow_surf, glow_rect)
            
            # Основная карточка
            card_color = (55, 60, 80) if is_hover else (35, 40, 60)
            pygame.draw.rect(screen, card_color, card_rect, border_radius=20)
            
            border_color = COLORS["player"] if is_hover else COLORS["card_border"]
            border_width = 4 if is_hover else 3
            pygame.draw.rect(screen, border_color, card_rect, border_width, border_radius=20)
            
            # Иконка режима
            icon_text = self.font_huge.render(mode_data["icon"], True, COLORS["player"])
            icon_rect = icon_text.get_rect(center=(card_rect.centerx, card_rect.y + 80))
            screen.blit(icon_text, icon_rect)
            
            # Название режима
            title_text = self.font_large.render(mode_data["title"], True, COLORS["player"] if is_hover else COLORS["ui"])
            title_rect = title_text.get_rect(center=(card_rect.centerx, card_rect.y + 160))
            screen.blit(title_text, title_rect)
            
            # Описание
            desc_text = self.font_small.render(mode_data["desc"], True, (180, 180, 200))
            desc_rect = desc_text.get_rect(center=(card_rect.centerx, card_rect.y + 200))
            screen.blit(desc_text, desc_rect)
            
            # Особенности режима
            feature_y = card_rect.y + 240
            for feature in mode_data["features"]:
                feature_text = self.font_tiny.render(f"- {feature}", True, (150, 150, 170))
                screen.blit(feature_text, (card_rect.x + 30, feature_y))
                feature_y += 25
            
            # Обработка нажатия
            if is_hover and mouse_clicked:
                self.game_mode = mode_data["mode"]
                self.reset_game()
                self.state = GameState.PLAY
                pygame.time.delay(200)
        
        # Кнопка назад
        back_rect = pygame.Rect(50, HEIGHT - 100, 200, 60)
        is_hover_back = back_rect.collidepoint(mouse_pos)
        
        color = COLORS["player"] if is_hover_back else COLORS["card_border"]
        pygame.draw.rect(screen, color, back_rect, 3, border_radius=8)
        
        text = self.font_small.render("НАЗАД", True, COLORS["player"])
        text_rect = text.get_rect(center=back_rect.center)
        screen.blit(text, text_rect)
        
        if is_hover_back and mouse_clicked:
            self.state = GameState.MENU
            pygame.time.delay(200)
    
    def draw_stats_menu(self):
        """Улучшенное меню статистики с красивым дизайном"""
        self._draw_submenu_bg()
        
        # Заголовок
        self.ui_draw_title("СТАТИСТИКА")
        
        # Единый контейнер
        container_w = self.CONTAINER_W
        container_x = WIDTH // 2 - container_w // 2
        container_y = 110
        
        stats = self.save_system.data["stats"]
        
        # Статистика в красивых карточках
        stats_list = [
            ("Всего игр", f"{stats['games_played']}", COLORS["player"]),
            ("Всего убийств", f"{stats['total_kills']}", COLORS["enemy"]),
            ("Время игры", f"{stats['total_playtime']}s", COLORS["exp"]),
            ("Лучший счёт", f"{stats['best_score']}", COLORS["warning"]),
            ("Лучшее время", f"{stats['best_time']}s", COLORS["shield"]),
            ("Макс. уровень", f"{stats['max_level']}", COLORS["player"]),
            ("Макс. волна", f"{stats['max_wave']}", COLORS["health"])
        ]
        
        card_h = 75
        gap = 12
        total_h = len(stats_list) * (card_h + gap) + 20
        
        # Контейнер-рамка
        cont_rect = pygame.Rect(container_x - 10, container_y - 10, container_w + 20, total_h + 20)
        pygame.draw.rect(screen, (15, 18, 25), cont_rect, border_radius=12)
        pygame.draw.rect(screen, COLORS["card_border"], cont_rect, 2, border_radius=12)
        
        y = container_y
        
        for label, value, color in stats_list:
            card_rect = pygame.Rect(container_x, y, container_w, card_h)
            pygame.draw.rect(screen, (40, 50, 70), card_rect, border_radius=12)
            pygame.draw.rect(screen, color, card_rect, 2, border_radius=12)
            
            label_text = self.font_medium.render(label, True, COLORS["ui"])
            screen.blit(label_text, (card_rect.x + 30, card_rect.centery - label_text.get_height() // 2))
            
            value_card_w = 200
            value_card_h = 50
            value_card_rect = pygame.Rect(card_rect.right - value_card_w - 20,
                                          card_rect.centery - value_card_h // 2,
                                          value_card_w, value_card_h)
            pygame.draw.rect(screen, (55, 65, 85), value_card_rect, border_radius=10)
            pygame.draw.rect(screen, color, value_card_rect, 2, border_radius=10)
            
            value_text = self.font_medium.render(value, True, color)
            screen.blit(value_text, value_text.get_rect(center=value_card_rect.center))
            
            y += card_h + gap
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Кнопка сброса статистики
        reset_button_rect = pygame.Rect(WIDTH - 280, HEIGHT - 95, 230, 55)
        reset_hover = reset_button_rect.collidepoint(mouse_pos)
        
        pygame.draw.rect(screen, (50, 20, 20) if reset_hover else (35, 15, 15), reset_button_rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["enemy"], reset_button_rect, 2, border_radius=10)
        
        # Иконка слева в кнопке
        icon_x = reset_button_rect.x + 28
        icon_y_c = reset_button_rect.centery
        if not self.draw_icon("reset", icon_x, icon_y_c, 28):
            sym = self.font_small.render("X", True, COLORS["enemy"])
            screen.blit(sym, (icon_x - sym.get_width()//2, icon_y_c - sym.get_height()//2))
        
        reset_text = self.font_small.render("СБРОСИТЬ", True, COLORS["enemy"])
        screen.blit(reset_text, (reset_button_rect.x + 52, icon_y_c - reset_text.get_height()//2))
        
        if reset_hover and pygame.mouse.get_pressed()[0] and not self.show_stats_reset_confirmation:
            self.show_stats_reset_confirmation = True
            pygame.time.delay(200)
        
        # Диалог подтверждения сброса статистики
        if self.show_stats_reset_confirmation:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 190))
            screen.blit(overlay, (0, 0))
            
            dialog_w, dialog_h = 660, 360
            dialog_x = WIDTH // 2 - dialog_w // 2
            dialog_y = HEIGHT // 2 - dialog_h // 2
            dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_w, dialog_h)
            
            pygame.draw.rect(screen, (35, 20, 20), dialog_rect, border_radius=15)
            pygame.draw.rect(screen, COLORS["enemy"], dialog_rect, 3, border_radius=15)
            
            warn_title = self.font_large.render("ПОЛНЫЙ СБРОС ПРОГРЕССА", True, COLORS["enemy"])
            screen.blit(warn_title, warn_title.get_rect(center=(WIDTH // 2, dialog_y + 58)))
            
            for li, line in enumerate([
                "Будет удалено ВСЁ:",
                "• Статистика и рекорды",
                "• Вся валюта (до 0)",
                "• Все модули и способности",
                "• Все достижения и скины",
                "Это действие НЕЛЬЗЯ отменить!"
            ]):
                col = COLORS["enemy"] if li in (0, 5) else (210, 210, 230)
                t = self.font_small.render(line, True, col)
                screen.blit(t, t.get_rect(center=(WIDTH // 2, dialog_y + 115 + li * 32)))
            
            btn_y = dialog_y + dialog_h - 80
            btn_w, btn_h = 210, 55
            
            yes_rect = pygame.Rect(dialog_x + 80, btn_y, btn_w, btn_h)
            yes_hover = yes_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (180, 40, 40) if yes_hover else (130, 30, 30), yes_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS["enemy"], yes_rect, 3, border_radius=10)
            yt = self.font_medium.render("СБРОСИТЬ", True, (255, 255, 255))
            screen.blit(yt, yt.get_rect(center=yes_rect.center))
            
            no_rect = pygame.Rect(dialog_x + dialog_w - 80 - btn_w, btn_y, btn_w, btn_h)
            no_hover = no_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (45, 55, 75) if no_hover else (35, 42, 60), no_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS["player"], no_rect, 3, border_radius=10)
            nt = self.font_medium.render("ОТМЕНА", True, COLORS["ui"])
            screen.blit(nt, nt.get_rect(center=no_rect.center))
            
            if yes_hover and pygame.mouse.get_pressed()[0]:
                # Полный сброс всего прогресса
                default_stats = {
                    "games_played": 0, "total_kills": 0, "total_playtime": 0,
                    "best_score": 0, "best_time": 0, "max_level": 0, "max_wave": 0
                }
                self.save_system.data["stats"] = default_stats
                # Сброс валюты
                self.save_system.data["currency"] = 0
                # Сброс модулей
                self.save_system.data["modules"] = {
                    "health": 0, "damage": 0, "speed": 0, "fire_rate": 0, "crit": 0
                }
                # Сброс способностей
                self.save_system.data["owned_abilities"] = []
                self.save_system.data["active_ability"] = ""
                # Сброс достижений
                ach_default = {k: False for k in AchievementSystem.ACHIEVEMENTS}
                self.save_system.data["achievements"] = ach_default
                # Блокировка всех скинов кроме default
                self.save_system.data["unlocked_skins"] = ["default"]
                self.save_system.data["current_skin"] = "default"
                self.save_system.save()
                self.show_stats_reset_confirmation = False
                pygame.time.delay(200)
            
            if no_hover and pygame.mouse.get_pressed()[0]:
                self.show_stats_reset_confirmation = False
                pygame.time.delay(200)
        
        self.draw_back_button()
    
    def draw_settings_menu(self):
        """Меню настроек с прокруткой"""
        # Инициализация скролла
        if not hasattr(self, 'settings_scroll'):
            self.settings_scroll = 0
        
        self._draw_submenu_bg()
        
        # Заголовок
        self.ui_draw_title("НАСТРОЙКИ")
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        
        # Контейнер с прокруткой
        container_w = self.CONTAINER_W
        container_h = HEIGHT - 220
        container_x = WIDTH // 2 - container_w // 2
        container_y = 110
        container_rect = pygame.Rect(container_x, container_y, container_w, container_h)
        pygame.draw.rect(screen, (15, 18, 25), container_rect, border_radius=12)
        pygame.draw.rect(screen, COLORS["card_border"], container_rect, 2, border_radius=12)
        
        controls = self.save_system.data["controls"]
        settings = self.save_system.data["settings"]
        
        # Вычисляем полный размер контента
        num_controls = len(controls)
        content_h = 45 + num_controls * 65 + 30 + 60 + 70 + 80 + 70 + 40  # примерная высота
        max_scroll = max(0, content_h - container_h + 30)
        
        # Клавиши прокрутки
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.settings_scroll = max(0, self.settings_scroll - 5)
        if keys[pygame.K_DOWN]:
            self.settings_scroll = min(max_scroll, self.settings_scroll + 5)
        self.settings_scroll = max(0, min(max_scroll, self.settings_scroll))
        
        # Scroll surface
        scroll_surface = pygame.Surface((container_w - 4, content_h), pygame.SRCALPHA)
        
        inner_w = container_w - 40
        y = 15
        
        # === СЕКЦИЯ УПРАВЛЕНИЯ ===
        sec_bg = pygame.Rect(10, y, inner_w, 40)
        pygame.draw.rect(scroll_surface, (35, 45, 60), sec_bg, border_radius=8)
        sec_t = self.font_medium.render("УПРАВЛЕНИЕ", True, COLORS["player"])
        scroll_surface.blit(sec_t, (20, y + 8))
        y += 50
        
        control_names = {
            "up": ("ВВЕРХ", COLORS["player"]),
            "down": ("ВНИЗ", COLORS["player"]),
            "left": ("ВЛЕВО", COLORS["player"]),
            "right": ("ВПРАВО", COLORS["player"]),
            "dash": ("РЫВОК", COLORS["warning"]),
            "auto_fire_toggle": ("АВТОСТРЕЛЬБА", COLORS["exp"]),
            "ability": ("СПОСОБНОСТЬ", (100, 200, 255))
        }
        
        for key_name, (label, color) in control_names.items():
            key_val = controls[key_name]
            card_rect = pygame.Rect(10, y, inner_w, 55)
            pygame.draw.rect(scroll_surface, (40, 50, 70), card_rect, border_radius=10)
            pygame.draw.rect(scroll_surface, COLORS["card_border"], card_rect, 2, border_radius=10)
            
            label_t = self.font_small.render(label, True, color)
            scroll_surface.blit(label_t, (20, y + 15))
            
            btn_w, btn_h = 155, 40
            btn_x = inner_w - btn_w - 15
            btn_rect = pygame.Rect(btn_x, y + 8, btn_w, btn_h)
            
            # Map scroll coords for hover detection
            scroll_btn_rect = pygame.Rect(
                container_x + 2 + btn_x,
                container_y + 2 + y - self.settings_scroll,
                btn_w, btn_h
            )
            is_btn_hover = scroll_btn_rect.collidepoint(mouse_pos) and container_rect.collidepoint(mouse_pos)
            
            if is_btn_hover:
                pygame.draw.rect(scroll_surface, (55, 65, 85), btn_rect, border_radius=8)
                pygame.draw.rect(scroll_surface, COLORS["player"], btn_rect, 3, border_radius=8)
                if mouse_clicked and self.rebinding_key is None:
                    self.rebinding_key = key_name
                    pygame.time.delay(200)
            else:
                pygame.draw.rect(scroll_surface, (45, 55, 75), btn_rect, border_radius=8)
                pygame.draw.rect(scroll_surface, color, btn_rect, 2, border_radius=8)
            
            if self.rebinding_key == key_name:
                val_t = self.font_tiny.render(">> Нажмите клавишу <<", True, COLORS["warning"])
            else:
                val_t = self.font_small.render(pygame.key.name(key_val).upper(), True, COLORS["player"])
            scroll_surface.blit(val_t, val_t.get_rect(center=(btn_rect.centerx, btn_rect.centery)))
            
            y += 62
        
        y += 20
        
        # === СЕКЦИЯ ГЕЙМПЛЕЯ ===
        sec_bg2 = pygame.Rect(10, y, inner_w, 40)
        pygame.draw.rect(scroll_surface, (35, 45, 60), sec_bg2, border_radius=8)
        sec_t2 = self.font_medium.render("ГЕЙМПЛЕЙ", True, COLORS["player"])
        scroll_surface.blit(sec_t2, (20, y + 8))
        y += 50
        
        # Интервал волн (auto-fire убрана из настроек — используйте кнопку)
        interval_card = pygame.Rect(10, y, inner_w, 65)
        pygame.draw.rect(scroll_surface, (40, 50, 70), interval_card, border_radius=10)
        pygame.draw.rect(scroll_surface, COLORS["card_border"], interval_card, 2, border_radius=10)
        il = self.font_small.render("ИНТЕРВАЛ ВОЛН:", True, COLORS["ui"])
        scroll_surface.blit(il, (20, y + 10))
        slider_w = min(350, inner_w - 240)
        slider_x = 20
        slider_y_local = y + 42
        slider_h = 10
        current_duration = settings.get("wave_break_duration", 10)
        slider_pos = (current_duration - 3) / 27
        pygame.draw.rect(scroll_surface, (30, 35, 45), (slider_x, slider_y_local, slider_w, slider_h), border_radius=5)
        filled_w = int(slider_w * slider_pos)
        if filled_w > 0:
            pygame.draw.rect(scroll_surface, COLORS["player"], (slider_x, slider_y_local, filled_w, slider_h), border_radius=5)
        handle_x_local = slider_x + int(slider_pos * slider_w)
        pygame.draw.circle(scroll_surface, COLORS["player"], (handle_x_local, slider_y_local + slider_h // 2), 12)
        # Slider interaction
        slider_screen_rect = pygame.Rect(container_x + 2 + slider_x, container_y + 2 + slider_y_local - 12 - self.settings_scroll, slider_w, slider_h + 24)
        if slider_screen_rect.collidepoint(mouse_pos) and container_rect.collidepoint(mouse_pos) and mouse_clicked:
            rel_x = max(0, min(slider_w, mouse_pos[0] - (container_x + 2 + slider_x)))
            new_pos = rel_x / slider_w
            settings["wave_break_duration"] = int(3 + new_pos * 27)
            self.save_system.save()
        val_t = self.font_medium.render(f"{current_duration}с", True, COLORS["player"])
        scroll_surface.blit(val_t, (inner_w - 70, y + 30))
        y += 75
        
        # Курсор
        cursor_card = pygame.Rect(10, y, inner_w, 55)
        pygame.draw.rect(scroll_surface, (40, 50, 70), cursor_card, border_radius=10)
        pygame.draw.rect(scroll_surface, COLORS["card_border"], cursor_card, 2, border_radius=10)
        cl = self.font_small.render("УКАЗАТЕЛЬ МЫШИ:", True, COLORS["ui"])
        scroll_surface.blit(cl, (20, y + 15))
        cursor_mode = settings.get("cursor_mode", "game")
        cur_opts = [("Игровой", "game"), ("Системный", "system")]
        for ci, (clabel, cval) in enumerate(cur_opts):
            cbr = pygame.Rect(inner_w - 285 + ci * 140, y + 8, 128, 38)
            is_active_cur = cursor_mode == cval
            cbg = COLORS["player"] if is_active_cur else (45, 55, 72)
            pygame.draw.rect(scroll_surface, cbg, cbr, border_radius=8)
            pygame.draw.rect(scroll_surface, COLORS["player"] if is_active_cur else COLORS["card_border"], cbr, 2, border_radius=8)
            ct = self.font_tiny.render(clabel, True, COLORS["bg"] if is_active_cur else COLORS["ui"])
            scroll_surface.blit(ct, ct.get_rect(center=cbr.center))
            # Click
            cbr_screen = pygame.Rect(container_x + 2 + inner_w - 285 + ci * 140, container_y + 2 + y + 8 - self.settings_scroll, 128, 38)
            if cbr_screen.collidepoint(mouse_pos) and container_rect.collidepoint(mouse_pos) and mouse_clicked and not is_active_cur:
                settings["cursor_mode"] = cval
                self.save_system.save()
                pygame.time.delay(150)
        y += 62
        
        # Сброс прогресса
        y += 10
        reset_card = pygame.Rect(10, y, inner_w, 55)
        pygame.draw.rect(scroll_surface, (45, 25, 25), reset_card, border_radius=10)
        pygame.draw.rect(scroll_surface, COLORS["enemy"], reset_card, 2, border_radius=10)
        reset_t = self.font_small.render("СБРОСИТЬ ПРОГРЕСС", True, COLORS["enemy"])
        scroll_surface.blit(reset_t, reset_t.get_rect(center=(inner_w // 2, y + 27)))
        reset_screen = pygame.Rect(container_x + 2 + 10, container_y + 2 + y - self.settings_scroll, inner_w, 55)
        if reset_screen.collidepoint(mouse_pos) and container_rect.collidepoint(mouse_pos) and mouse_clicked:
            if not getattr(self, 'show_stats_reset_confirmation', False):
                self.show_stats_reset_confirmation = True
                pygame.time.delay(150)
        y += 65
        
        # Отрисовка scroll_surface
        clip_r = pygame.Rect(container_x + 2, container_y + 2, container_w - 4, container_h - 4)
        screen.set_clip(clip_r)
        screen.blit(scroll_surface, (container_x + 2, container_y + 2 - self.settings_scroll))
        screen.set_clip(None)
        
        # Scrollbar
        if max_scroll > 0:
            sb_h = max(40, int((container_h / content_h) * container_h))
            sb_y = container_y + 2 + int((self.settings_scroll / max_scroll) * (container_h - sb_h - 4))
            pygame.draw.rect(screen, COLORS["player"], (container_x + container_w - 12, sb_y, 8, sb_h), border_radius=4)
        
        # Диалог подтверждения сброса
        if getattr(self, 'show_stats_reset_confirmation', False):
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            dialog_w, dialog_h = 500, 220
            dialog_x = WIDTH // 2 - dialog_w // 2
            dialog_y = HEIGHT // 2 - dialog_h // 2
            dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_w, dialog_h)
            pygame.draw.rect(screen, (30, 20, 20), dialog_rect, border_radius=16)
            pygame.draw.rect(screen, COLORS["enemy"], dialog_rect, 3, border_radius=16)
            conf_t = self.font_medium.render("Сбросить весь прогресс?", True, COLORS["enemy"])
            screen.blit(conf_t, conf_t.get_rect(center=(WIDTH//2, dialog_y + 55)))
            sub_t = self.font_tiny.render("Статистика, скины и достижения будут удалены!", True, (200,180,180))
            screen.blit(sub_t, sub_t.get_rect(center=(WIDTH//2, dialog_y + 90)))
            btn_y = dialog_y + 130
            btn_w, btn_h = 190, 50
            yes_rect = pygame.Rect(dialog_x + 50, btn_y, btn_w, btn_h)
            yes_h = yes_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (180,40,40) if yes_h else (130,30,30), yes_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS["enemy"], yes_rect, 3, border_radius=10)
            screen.blit(self.font_medium.render("СБРОСИТЬ", True, (255,255,255)), self.font_medium.render("СБРОСИТЬ", True, (255,255,255)).get_rect(center=yes_rect.center))
            no_rect = pygame.Rect(dialog_x + dialog_w - 50 - btn_w, btn_y, btn_w, btn_h)
            no_h = no_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (45,55,75) if no_h else (35,42,60), no_rect, border_radius=10)
            pygame.draw.rect(screen, COLORS["player"], no_rect, 3, border_radius=10)
            screen.blit(self.font_medium.render("ОТМЕНА", True, COLORS["ui"]), self.font_medium.render("ОТМЕНА", True, COLORS["ui"]).get_rect(center=no_rect.center))
            if yes_h and mouse_clicked:
                self.save_system.data["stats"] = {"games_played":0,"total_kills":0,"total_playtime":0,"best_score":0,"best_time":0,"max_level":0,"max_wave":0}
                self.save_system.data["unlocked_skins"] = ["default"]
                self.save_system.data["current_skin"] = "default"
                # Сброс валюты, модулей и способностей
                self.save_system.data["currency"] = 0
                self.save_system.data["modules"] = {"health":0,"damage":0,"speed":0,"fire_rate":0,"crit":0}
                self.save_system.data["owned_abilities"] = []
                self.save_system.data["active_ability"] = ""
                # Сброс достижений
                ach_default = {k: False for k in AchievementSystem.ACHIEVEMENTS}
                self.save_system.data["achievements"] = ach_default
                if "achievement_rewards_claimed" in self.save_system.data:
                    self.save_system.data["achievement_rewards_claimed"] = {}
                self.save_system.save()
                self.show_stats_reset_confirmation = False
                pygame.time.delay(200)
            if no_h and mouse_clicked:
                self.show_stats_reset_confirmation = False
                pygame.time.delay(200)
        
        self.draw_back_button()
    
    def draw_modules_menu(self):
        """МАГАЗИН: вкладки Модули и Способности"""
        # Init tab state
        if not hasattr(self, 'shop_tab'):
            self.shop_tab = "modules"
        
        # Фон с градиентом + точки
        for _i in range(HEIGHT):
            _p = _i / HEIGHT
            pygame.draw.line(screen, (int(7+14*_p), int(9+18*_p), int(18+30*_p)), (0,_i),(WIDTH,_i))
        for _dx in range(0, WIDTH + 50, 50):
            for _dy in range(0, HEIGHT + 50, 50):
                pygame.draw.circle(screen, (20, 26, 44), (_dx, _dy), 2)
        
        # Заголовок
        title = self.font_large.render("МАГАЗИН", True, COLORS["player"])
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 50)))
        
        # Валюта
        currency = self.save_system.data["currency"]
        curr_card = pygame.Rect(WIDTH - 280, 20, 260, 50)
        pygame.draw.rect(screen, (35, 42, 60), curr_card, border_radius=10)
        pygame.draw.rect(screen, COLORS["warning"], curr_card, 2, border_radius=10)
        curr_t = self.font_medium.render(f"$ {currency}", True, COLORS["warning"])
        screen.blit(curr_t, curr_t.get_rect(center=curr_card.center))
        
        # Вкладки
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        tab_defs = [("modules", "МОДУЛИ"), ("abilities", "СПОСОБНОСТИ")]
        tab_w, tab_h = 240, 44
        tab_y = 90
        tab_sx = WIDTH // 2 - (tab_w * 2 + 15) // 2
        for ti, (tid, tname) in enumerate(tab_defs):
            tr = pygame.Rect(tab_sx + ti * (tab_w + 15), tab_y, tab_w, tab_h)
            is_active = self.shop_tab == tid
            pygame.draw.rect(screen, (50, 65, 90) if is_active else (28, 35, 52), tr, border_radius=10)
            pygame.draw.rect(screen, COLORS["player"] if is_active else COLORS["card_border"], tr, 2 if not is_active else 3, border_radius=10)
            _tab_surf = self.font_small.render(tname, True, COLORS["player"] if is_active else COLORS["ui"])
            screen.blit(_tab_surf, _tab_surf.get_rect(center=tr.center))
            if tr.collidepoint(mouse_pos) and mouse_clicked and not is_active:
                self.shop_tab = tid
                pygame.time.delay(150)
        
        # Summary stats bar
        modules = self.save_system.data["modules"]
        total_hp = 100 + modules.get("health", 0) * 10
        total_dmg = 10 + modules.get("damage", 0) * 2
        total_speed = 6.5 + modules.get("speed", 0) * 0.5
        total_fire_rate = max(100, 250 - modules.get("fire_rate", 0) * 5)
        total_crit = 0.1 + modules.get("crit", 0) * 0.02
        
        sum_w = 1000
        sum_x = WIDTH // 2 - sum_w // 2
        sum_y = 148
        sum_rect = pygame.Rect(sum_x, sum_y, sum_w, 52)
        pygame.draw.rect(screen, (30, 36, 52), sum_rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["player"], sum_rect, 1, border_radius=10)
        ss = [(f"HP:{total_hp}", COLORS["health"]), (f"УРН:{total_dmg}", COLORS["enemy"]),
              (f"СКР:{total_speed:.1f}", COLORS["player"]), (f"ОГН:{total_fire_rate}мс", COLORS["warning"]),
              (f"КРТ:{int(total_crit*100)}%", COLORS["exp"])]
        sw = sum_w // len(ss)
        for si, (st, sc) in enumerate(ss):
            tx = sum_x + si * sw + sw // 2
            _sst = self.font_tiny.render(st, True, sc)
            screen.blit(_sst, _sst.get_rect(center=(tx, sum_rect.centery)))
        
        cont_x = WIDTH // 2 - self.CONTAINER_W // 2
        cont_y = 215
        cont_w = self.CONTAINER_W
        
        if self.shop_tab == "modules":
            # ---- MODULES TAB ----
            module_info = {
                "health":    {"name": "ЗДОРОВЬЕ",        "cost": 50,  "desc": "+10 макс. HP",          "icon": "[HP]",  "color": COLORS["health"]},
                "damage":    {"name": "УРОН",             "cost": 50,  "desc": "+2 урон за выстрел",    "icon": "[DMG]", "color": COLORS["enemy"]},
                "speed":     {"name": "СКОРОСТЬ",         "cost": 50,  "desc": "+0.5 скорость движения","icon": "[SPD]", "color": COLORS["player"]},
                "fire_rate": {"name": "СКОРОСТРЕЛЬНОСТЬ", "cost": 75,  "desc": "-5мс перезарядка",      "icon": "[FR]",  "color": COLORS["warning"]},
                "crit":      {"name": "КРИТ. УДАР",       "cost": 100, "desc": "+2% крит шанс",         "icon": "[CRT]", "color": COLORS["exp"]},
            }
            
            MAX_MODULE_LEVEL = 10
            y = cont_y
            for mod_id, info in module_info.items():
                level = modules.get(mod_id, 0)
                cost = info["cost"] * (level + 1)
                can_afford = currency >= cost and level < MAX_MODULE_LEVEL
                
                card_h = 78
                brect = pygame.Rect(cont_x, y, cont_w, card_h)
                is_hover = brect.collidepoint(mouse_pos)
                
                bg = (52, 62, 82) if (is_hover and can_afford) else ((38, 46, 66) if can_afford else (28, 32, 46))
                border = info["color"] if (is_hover and can_afford) else (COLORS["card_border"] if can_afford else (55,55,70))
                bw = 3 if (is_hover and can_afford) else 2
                pygame.draw.rect(screen, bg, brect, border_radius=12)
                pygame.draw.rect(screen, border, brect, bw, border_radius=12)
                
                # Icon
                ict = self.font_small.render(info["icon"], True, info["color"])
                screen.blit(ict, (brect.x + 15, brect.centery - ict.get_height() // 2))
                
                # 10-pip progress bar
                pip_start_x = brect.x + 90
                pip_y = brect.y + 12
                pip_w, pip_h = 22, 14
                pip_gap = 4
                for pip_i in range(MAX_MODULE_LEVEL):
                    px = pip_start_x + pip_i * (pip_w + pip_gap)
                    filled_pip = pip_i < level
                    pip_col = info["color"] if filled_pip else (35, 40, 55)
                    pip_border = info["color"] if filled_pip else (55, 60, 75)
                    pygame.draw.rect(screen, pip_col, (px, pip_y, pip_w, pip_h), border_radius=3)
                    pygame.draw.rect(screen, pip_border, (px, pip_y, pip_w, pip_h), 1, border_radius=3)
                
                # Name + level
                nt = self.font_small.render(f"{info['name']}  Ур.{level}/{MAX_MODULE_LEVEL}", True, COLORS["ui"] if can_afford or level >= MAX_MODULE_LEVEL else (110,110,125))
                screen.blit(nt, (pip_start_x, brect.y + 30))
                dt = self.font_tiny.render(info["desc"], True, (160,165,185))
                screen.blit(dt, (pip_start_x, brect.y + 55))
                
                # Cost badge
                cbx = brect.right - 130
                cby = brect.centery - 20
                cbrect = pygame.Rect(cbx, cby, 115, 40)
                if level >= MAX_MODULE_LEVEL:
                    pygame.draw.rect(screen, (45,42,18), cbrect, border_radius=8)
                    pygame.draw.rect(screen, COLORS["warning"], cbrect, 2, border_radius=8)
                    _mt = self.font_tiny.render("МАКС", True, COLORS["warning"]); screen.blit(_mt, _mt.get_rect(center=cbrect.center))
                else:
                    cbc = (45,55,72) if can_afford else (32,36,50)
                    ccc = COLORS["player"] if can_afford else (100,100,110)
                    pygame.draw.rect(screen, cbc, cbrect, border_radius=8)
                    pygame.draw.rect(screen, ccc, cbrect, 2, border_radius=8)
                    _ct = self.font_small.render(f"$ {cost}", True, ccc); screen.blit(_ct, _ct.get_rect(center=cbrect.center))
                
                if is_hover and mouse_clicked and can_afford and not getattr(self, '_mod_click', False):
                    self._mod_click = True
                    modules[mod_id] = level + 1
                    self.save_system.data["currency"] -= cost
                    self.save_system.save()
                    pygame.time.delay(150)
                
                y += card_h + 10
        
        else:
            # ---- ABILITIES TAB ----
            # Все способности активируются одной кнопкой [Q] - только одна может быть активна
            ABILITIES = [
                {"id": "dash_boost",   "name": "РЫВОК-УДАР",        "cost": 100, "color": COLORS["player"],
                 "desc": "Рывок наносит 30 урона всем врагам на пути. Перезарядка: пассивный эффект.",
                 "icon": "[>>]"},
                {"id": "shield_pulse", "name": "ИМПУЛЬС ЩИТА",      "cost": 250, "color": COLORS["shield"],
                 "desc": "Взрыв отталкивает всех врагов в радиусе 250px. КД: 6с.",
                 "icon": "[()]"},
                {"id": "time_slow",    "name": "ЗАМЕДЛЕНИЕ",         "cost": 350, "color": (100, 200, 255),
                 "desc": "Замедляет всех врагов на 60% на 4 секунды. КД: 12с.",
                 "icon": "[<<]"},
                {"id": "overdrive",    "name": "ПЕРЕГРУЗКА",         "cost": 300, "color": COLORS["warning"],
                 "desc": "+100% скорострельность на 5с. КД: 15с.",
                 "icon": "[!!]"},
                {"id": "nuke",         "name": "ЯДЕРНЫЙ ЗАРЯД",     "cost": 500, "color": COLORS["enemy"],
                 "desc": "Взрыв радиус 400px, 150 урона всем врагам. КД: 20с.",
                 "icon": "[*]"},
                {"id": "heal_pulse",   "name": "ПУЛЬС ИСЦЕЛЕНИЯ",   "cost": 400, "color": (100, 255, 150),
                 "desc": "Восстанавливает 40% HP и создаёт щит на 3с. КД: 18с.",
                 "icon": "[+]"},
                {"id": "bullet_storm", "name": "ШТОРМ ПУЛЬ",        "cost": 450, "color": (255, 180, 50),
                 "desc": "Выпускает 24 пули во все стороны. КД: 10с.",
                 "icon": "[x]"},
            ]
            
            # Подсказка
            ability_key_val = self.save_system.data["controls"].get("ability", pygame.K_q)
            ability_key_name = pygame.key.name(ability_key_val).upper()
            hint_ab = self.font_tiny.render(f"Активная способность: [{ability_key_name}] — только одна может быть активна одновременно. Кнопку можно изменить в Настройках.", True, (150, 160, 180))
            screen.blit(hint_ab, hint_ab.get_rect(center=(WIDTH // 2, cont_y - 12)))
            
            owned = self.save_system.data.get("owned_abilities", [])
            active = self.save_system.data.get("active_ability", "")
            
            y = cont_y
            for ab in ABILITIES:
                ab_id = ab["id"]
                is_owned = ab_id in owned
                is_active = ab_id == active
                
                card_h = 90
                brect = pygame.Rect(cont_x, y, cont_w, card_h)
                is_hover = brect.collidepoint(mouse_pos)
                
                bg = (50, 65, 80) if is_active else ((42, 52, 68) if (is_hover and is_owned) else ((38, 46, 62) if is_owned else (24, 28, 42)))
                border = ab["color"] if is_active else (ab["color"] if is_hover else (COLORS["card_border"] if is_owned else (50, 55, 68)))
                pygame.draw.rect(screen, bg, brect, border_radius=12)
                pygame.draw.rect(screen, border, brect, 3 if is_active else 2, border_radius=12)
                
                # Icon
                ict = self.font_medium.render(ab["icon"], True, ab["color"] if is_owned else (80,80,95))
                screen.blit(ict, (brect.x + 15, brect.centery - ict.get_height() // 2))
                
                # [Q] badge (только у активной)
                if is_active:
                    kb = pygame.Rect(brect.x + 75, brect.y + 27, 38, 38)
                    pygame.draw.rect(screen, (35, 45, 60), kb, border_radius=8)
                    pygame.draw.rect(screen, ab["color"], kb, 2, border_radius=8)
                    _kbt = self.font_small.render("Q", True, ab["color"])
                    screen.blit(_kbt, _kbt.get_rect(center=kb.center))
                
                # Name + desc
                nc = ab["color"] if is_owned else (130,130,145)
                tx0 = brect.x + 120 if is_active else brect.x + 75
                screen.blit(self.font_small.render(ab["name"], True, nc), (tx0, brect.y + 12))
                screen.blit(self.font_tiny.render(ab["desc"], True, (160,165,185) if is_owned else (100,105,120)), (tx0, brect.y + 44))
                
                # Active badge
                if is_active:
                    act_t = self.font_tiny.render("[АКТИВНА — нажмите Q в бою]", True, ab["color"])
                    screen.blit(act_t, (tx0, brect.y + 68))
                
                # Right button
                if is_owned:
                    if not is_active:
                        sb = pygame.Rect(brect.right - 140, brect.centery - 18, 125, 36)
                        sbg = (50, 65, 82) if brect.collidepoint(mouse_pos) else (38,48,64)
                        pygame.draw.rect(screen, sbg, sb, border_radius=8)
                        pygame.draw.rect(screen, ab["color"], sb, 2, border_radius=8)
                        _sbt = self.font_tiny.render("ВЫБРАТЬ", True, ab["color"]); screen.blit(_sbt, _sbt.get_rect(center=sb.center))
                        if sb.collidepoint(mouse_pos) and mouse_clicked and not getattr(self, '_ab_click', False):
                            self._ab_click = True
                            self.save_system.data["active_ability"] = ab_id
                            self.save_system.save()
                            pygame.time.delay(150)
                else:
                    can_buy = currency >= ab["cost"]
                    sb = pygame.Rect(brect.right - 150, brect.centery - 20, 135, 40)
                    sbg = (40,55,72) if (is_hover and can_buy) else ((30,36,50) if can_buy else (22,26,38))
                    sbc = ab["color"] if can_buy else (60,60,72)
                    pygame.draw.rect(screen, sbg, sb, border_radius=8)
                    pygame.draw.rect(screen, sbc, sb, 2, border_radius=8)
                    _cbt = self.font_small.render(f"$ {ab['cost']}", True, sbc); screen.blit(_cbt, _cbt.get_rect(center=sb.center))
                    if sb.collidepoint(mouse_pos) and mouse_clicked and can_buy and not getattr(self, '_ab_click', False):
                        self._ab_click = True
                        owned.append(ab_id)
                        self.save_system.data["owned_abilities"] = owned
                        self.save_system.data["currency"] -= ab["cost"]
                        if not active:
                            self.save_system.data["active_ability"] = ab_id
                        self.save_system.save()
                        pygame.time.delay(150)
                
                y += card_h + 10
        
        self.draw_back_button()
    
    def draw_skins_menu(self):
        """Скины - контейнер со скроллом как у достижений"""
        # Единый фон подменю
        for _i in range(HEIGHT):
            _p = _i / HEIGHT
            pygame.draw.line(screen, (int(7+14*_p), int(9+18*_p), int(18+30*_p)), (0,_i),(WIDTH,_i))
        for _dx in range(0, WIDTH + 50, 50):
            for _dy in range(0, HEIGHT + 50, 50):
                pygame.draw.circle(screen, (20, 26, 44), (_dx, _dy), 2)
        title = self.font_large.render("СКИНЫ ПЕРСОНАЖА", True, COLORS["player"])
        title_rect = title.get_rect(center=(WIDTH // 2, 60))
        # Свечение заголовка
        glow_surf = pygame.Surface((title_rect.width + 40, title_rect.height + 40), pygame.SRCALPHA)
        for gi in range(3):
            alpha = 35 - gi * 10
            glow_t = self.font_large.render("СКИНЫ ПЕРСОНАЖА", True, (*COLORS["player_glow"], alpha))
            glow_surf.blit(glow_t, (20 + gi * 2, 20 + gi * 2))
        screen.blit(glow_surf, (title_rect.x - 20, title_rect.y - 20))
        screen.blit(title, title_rect)

        # Проверка разблокировок (обновлённые требования)
        unlocked = self.save_system.data["unlocked_skins"]
        current = self.save_system.data["current_skin"]
        stats = self.save_system.data["stats"]
        if stats["total_kills"] >= 500 and "red" not in unlocked:
            unlocked.append("red"); self.save_system.save()
        if stats["max_level"] >= 15 and "purple" not in unlocked:
            unlocked.append("purple"); self.save_system.save()
        if stats["best_score"] >= 10000 and "gold" not in unlocked:
            unlocked.append("gold"); self.save_system.save()
        if stats["best_time"] >= 600 and "green" not in unlocked:
            unlocked.append("green"); self.save_system.save()
        # cyan: 50 достижений — через achievements count
        ach_count = sum(1 for v in self.save_system.data["achievements"].values() if v)
        if ach_count >= 30 and "cyan" not in unlocked:
            unlocked.append("cyan"); self.save_system.save()
        if stats["total_kills"] >= 2000 and "orange" not in unlocked:
            unlocked.append("orange"); self.save_system.save()
        if stats["max_level"] >= 25 and "white" not in unlocked:
            unlocked.append("white"); self.save_system.save()
        if getattr(self, 'dash_count', 0) >= 100 and "pink" not in unlocked:
            unlocked.append("pink"); self.save_system.save()
        if stats["total_kills"] >= 5000 and "dark" not in unlocked:
            unlocked.append("dark"); self.save_system.save()

        # Инициализация скролла
        if not hasattr(self, 'skins_scroll'):
            self.skins_scroll = 0

        # Размеры контейнера
        container_w = self.CONTAINER_W
        container_h = HEIGHT - 280
        container_x = WIDTH // 2 - container_w // 2
        container_y = 140
        container_rect = pygame.Rect(container_x, container_y, container_w, container_h)

        # Фон контейнера
        pygame.draw.rect(screen, (15, 18, 25), container_rect, border_radius=12)
        pygame.draw.rect(screen, COLORS["card_border"], container_rect, 2, border_radius=12)

        # Подсчёт высоты контента
        card_h_unlocked = 100
        card_h_locked = 70
        card_spacing = 12
        total_content_h = sum(
            card_h_unlocked + card_spacing if sk in unlocked else card_h_locked + card_spacing
            for sk in PLAYER_SKINS
        )
        max_scroll = max(0, total_content_h - container_h + 40)
        # Зажим скролла
        self.skins_scroll = max(0, min(max_scroll, self.skins_scroll))

        # Прокрутка клавишами
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.skins_scroll = max(0, self.skins_scroll - 5)
        if keys[pygame.K_DOWN]:
            self.skins_scroll = min(max_scroll, self.skins_scroll + 5)

        # Рисуем скины напрямую на экран с клиппингом (надёжнее scroll_surface)
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]

        clip_rect = pygame.Rect(container_x + 2, container_y + 2, container_w - 4, container_h - 4)
        screen.set_clip(clip_rect)

        y_screen = container_y + 15 - self.skins_scroll

        for skin_id, skin_data in PLAYER_SKINS.items():
            is_unlocked = skin_id in unlocked
            is_current = skin_id == current
            card_h = card_h_unlocked if is_unlocked else card_h_locked

            # Пропуск вне видимости
            if y_screen + card_h < container_y or y_screen > container_y + container_h:
                y_screen += card_h + card_spacing
                continue

            card_w = container_w - 30
            card_rect = pygame.Rect(container_x + 10, y_screen, card_w, card_h)

            # Карточка
            if is_current:
                card_color = (45, 60, 80)
            elif is_unlocked:
                card_color = (35, 42, 58)
            else:
                card_color = (22, 26, 36)
            pygame.draw.rect(screen, card_color, card_rect, border_radius=12)

            if is_current:
                border_color = skin_data["color"]
                border_w = 3
            elif is_unlocked:
                border_color = (160, 160, 200)
                border_w = 2
            else:
                border_color = (60, 65, 80)
                border_w = 1
            pygame.draw.rect(screen, border_color, card_rect, border_w, border_radius=12)

            # Превью корабля
            if skin_id == "default":
                pts = [(28,0),(18,-6),(-15,-12),(-10,0),(-15,12),(18,6)]
            elif skin_id == "red":
                pts = [(30,0),(12,-10),(-12,-15),(-8,0),(-12,15),(12,10)]
            elif skin_id == "purple":
                pts = [(26,0),(18,-5),(8,-8),(-16,-6),(-16,6),(8,8),(18,5)]
            elif skin_id == "gold":
                pts = [(24,0),(15,-12),(-6,-16),(-15,-8),(-15,8),(-6,16),(15,12)]
            elif skin_id == "green":
                pts = [(32,0),(20,-4),(10,-12),(-10,-10),(-15,0),(-10,10),(10,12),(20,4)]
            elif skin_id == "cyan":
                pts = [(32,0),(16,-10),(5,-5),(-12,-16),(-9,0),(-12,16),(5,5),(16,10)]
            elif skin_id == "orange":
                pts = [(19,0),(12,-17),(-3,-21),(-17,-14),(-17,14),(-3,21),(12,17)]
            elif skin_id == "white":
                import math as _m
                pts = [(_m.cos(_m.radians(-90+i*36))*(28 if i%2==0 else 14),
                        _m.sin(_m.radians(-90+i*36))*(28 if i%2==0 else 14)) for i in range(10)]
            elif skin_id == "pink":
                pts = [(35,0),(19,-3),(4,-17),(-7,-7),(-15,0),(-7,7),(4,17),(19,3)]
            elif skin_id == "dark":
                pts = [(24,-12),(24,12),(12,22),(-8,19),(-20,7),(-20,-7),(-8,-19),(12,-22)]
            else:
                pts = [(28,0),(18,-6),(-15,-12),(-10,0),(-15,12),(18,6)]
            
            pcx = card_rect.x + card_h // 2
            pcy = card_rect.centery
            col = skin_data["color"] if is_unlocked else (80, 80, 90)
            sc_pts = [(pcx + p[0]*0.7, pcy + p[1]*0.7) for p in pts]
            pygame.draw.polygon(screen, col, sc_pts)
            pygame.draw.polygon(screen, skin_data["glow"] if is_unlocked else (60,60,70), sc_pts, 2)

            # Название
            name_col = skin_data["color"] if is_unlocked else (110, 110, 120)
            name_text = self.font_small.render(skin_data["name"], True, name_col)
            screen.blit(name_text, (card_rect.x + card_h + 10, card_rect.y + 10))

            # Условие
            cond_text = self.font_tiny.render(skin_data["condition"], True, (160, 165, 185))
            screen.blit(cond_text, (card_rect.x + card_h + 10, card_rect.y + 38))

            # Эффект (только открытые)
            if is_unlocked:
                eff_text = self.font_tiny.render(f"Эффект: {skin_data['effect']}", True, COLORS["warning"])
                screen.blit(eff_text, (card_rect.x + card_h + 10, card_rect.y + 62))

            # Кнопка / замок
            if is_unlocked:
                btn_rect = pygame.Rect(card_rect.right - 135, card_rect.centery - 18, 115, 36)
                is_hover_btn = btn_rect.collidepoint(mouse_pos) and clip_rect.collidepoint(mouse_pos)

                if is_current:
                    pygame.draw.rect(screen, COLORS["player"], btn_rect, border_radius=8)
                    bt = self.font_tiny.render("АКТИВЕН", True, COLORS["bg"])
                else:
                    bc = (55, 65, 85) if is_hover_btn else (38, 45, 62)
                    pygame.draw.rect(screen, bc, btn_rect, border_radius=8)
                    pygame.draw.rect(screen, COLORS["player"] if is_hover_btn else COLORS["card_border"],
                                     btn_rect, 2, border_radius=8)
                    bt = self.font_tiny.render("ВЫБРАТЬ", True, COLORS["player"])
                screen.blit(bt, bt.get_rect(center=btn_rect.center))

                if is_hover_btn and mouse_clicked and not is_current:
                    if not getattr(self, '_skin_click_handled', False):
                        self._skin_click_handled = True
                        self.save_system.data["current_skin"] = skin_id
                        self.save_system.save()
                        pygame.time.delay(150)
            else:
                lock_t = self.font_tiny.render("[ЗАКРЫТ]", True, (90, 90, 100))
                screen.blit(lock_t, (card_rect.right - 110, card_rect.centery - 8))

            y_screen += card_h + card_spacing

        screen.set_clip(None)

        # Полоса прокрутки (внутри контейнера)
        if max_scroll > 0:
            sb_h = max(40, int((container_h / total_content_h) * container_h))
            sb_y = container_y + 2 + int((self.skins_scroll / max_scroll) * (container_h - sb_h - 4))
            sb_y = max(container_y + 2, min(container_y + container_h - sb_h - 2, sb_y))
            sb_rect = pygame.Rect(container_x + container_w - 12, sb_y, 8, sb_h)
            pygame.draw.rect(screen, (40, 45, 65), sb_rect, border_radius=4)
            pygame.draw.rect(screen, COLORS["player"], sb_rect, border_radius=4)

        # Подсказка
        hint = self.font_tiny.render("Используйте стрелки или колесо мыши для прокрутки", True, (110, 115, 135))
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 120))

        self.draw_back_button()
    
    def draw_ship_preview(self, x, y, skin_id, skin_data, scale=1.0):
        """Отрисовка превью корабля"""
        center = pygame.Vector2(x, y)
        
        # Разные формы для каждого скина
        if skin_id == "default":
            pts = [pygame.Vector2(28, 0), pygame.Vector2(18, -6), pygame.Vector2(-15, -12), 
                   pygame.Vector2(-10, 0), pygame.Vector2(-15, 12), pygame.Vector2(18, 6)]
        elif skin_id == "red":
            pts = [pygame.Vector2(30, 0), pygame.Vector2(12, -10), pygame.Vector2(-12, -15), 
                   pygame.Vector2(-8, 0), pygame.Vector2(-12, 15), pygame.Vector2(12, 10)]
        elif skin_id == "purple":
            pts = [pygame.Vector2(26, 0), pygame.Vector2(18, -5), pygame.Vector2(8, -8), 
                   pygame.Vector2(-16, -6), pygame.Vector2(-16, 6), pygame.Vector2(8, 8), pygame.Vector2(18, 5)]
        elif skin_id == "gold":
            pts = [pygame.Vector2(24, 0), pygame.Vector2(15, -12), pygame.Vector2(-6, -16), 
                   pygame.Vector2(-15, -8), pygame.Vector2(-15, 8), pygame.Vector2(-6, 16), pygame.Vector2(15, 12)]
        elif skin_id == "green":
            pts = [pygame.Vector2(32, 0), pygame.Vector2(20, -4), pygame.Vector2(10, -12), 
                   pygame.Vector2(-10, -10), pygame.Vector2(-15, 0), pygame.Vector2(-10, 10), 
                   pygame.Vector2(10, 12), pygame.Vector2(20, 4)]
        elif skin_id == "cyan":
            pts = [pygame.Vector2(32,0),pygame.Vector2(16,-10),pygame.Vector2(5,-5),pygame.Vector2(-12,-16),
                   pygame.Vector2(-9,0),pygame.Vector2(-12,16),pygame.Vector2(5,5),pygame.Vector2(16,10)]
        elif skin_id == "orange":
            pts = [pygame.Vector2(19,0),pygame.Vector2(12,-17),pygame.Vector2(-3,-21),
                   pygame.Vector2(-17,-14),pygame.Vector2(-17,14),pygame.Vector2(-3,21),pygame.Vector2(12,17)]
        elif skin_id == "white":
            pts = [pygame.Vector2(math.cos(math.radians(-90+i*36))*(28 if i%2==0 else 14),
                                  math.sin(math.radians(-90+i*36))*(28 if i%2==0 else 14)) for i in range(10)]
        elif skin_id == "pink":
            pts = [pygame.Vector2(35,0),pygame.Vector2(19,-3),pygame.Vector2(4,-17),pygame.Vector2(-7,-7),
                   pygame.Vector2(-15,0),pygame.Vector2(-7,7),pygame.Vector2(4,17),pygame.Vector2(19,3)]
        elif skin_id == "dark":
            pts = [pygame.Vector2(24,-12),pygame.Vector2(24,12),pygame.Vector2(12,22),pygame.Vector2(-8,19),
                   pygame.Vector2(-20,7),pygame.Vector2(-20,-7),pygame.Vector2(-8,-19),pygame.Vector2(12,-22)]
        else:
            pts = [pygame.Vector2(28, 0), pygame.Vector2(18, -6), pygame.Vector2(-15, -12), 
                   pygame.Vector2(-10, 0), pygame.Vector2(-15, 12), pygame.Vector2(18, 6)]
        
        scaled_pts = [(p * scale) + center for p in pts]
        pygame.draw.polygon(screen, skin_data["color"], scaled_pts)
        pygame.draw.polygon(screen, skin_data["glow"], scaled_pts, 2)
    
    def draw_achievements_menu(self):
        """Меню достижений с прокруткой"""
        for _i in range(HEIGHT):
            _p = _i / HEIGHT
            pygame.draw.line(screen, (int(7+14*_p), int(9+18*_p), int(18+30*_p)), (0,_i),(WIDTH,_i))
        for _dx in range(0, WIDTH + 50, 50):
            for _dy in range(0, HEIGHT + 50, 50):
                pygame.draw.circle(screen, (20, 26, 44), (_dx, _dy), 2)
        title = self.font_large.render("ДОСТИЖЕНИЯ", True, COLORS["player"])
        title_rect = title.get_rect(center=(WIDTH // 2, 60))
        screen.blit(title, title_rect)
        
        # Прогресс выполнения
        completed = sum(1 for v in self.save_system.data["achievements"].values() if v)
        total = len(AchievementSystem.ACHIEVEMENTS)
        progress_text = self.font_small.render(f"Выполнено: {completed}/{total}", True, COLORS["warning"])
        screen.blit(progress_text, (WIDTH // 2 - progress_text.get_width() // 2, 120))
        
        # Контейнер со скроллом
        container_w = self.CONTAINER_W
        container_h = HEIGHT - 290
        container_x = WIDTH // 2 - container_w // 2
        container_y = 180
        container_rect = pygame.Rect(container_x, container_y, container_w, container_h)
        
        # Фон контейнера
        pygame.draw.rect(screen, (15, 18, 25), container_rect, border_radius=12)
        pygame.draw.rect(screen, COLORS["card_border"], container_rect, 2, border_radius=12)
        
        # Вычисление полной высоты контента
        card_height = 90
        spacing = 15
        achievements_list = list(AchievementSystem.ACHIEVEMENTS.items())
        total_content_height = len(achievements_list) * (card_height + spacing)
        max_scroll = max(0, total_content_height - container_h + 40)
        
        # Обработка прокрутки колесиком мыши
        mouse_pos = pygame.mouse.get_pos()
        if container_rect.collidepoint(mouse_pos):
            keys = pygame.key.get_pressed()
            # Прокрутка колесиком (обрабатывается в event loop, здесь используем клавиши)
            if keys[pygame.K_UP]:
                self.achievements_scroll_offset = max(0, self.achievements_scroll_offset - 5)
            if keys[pygame.K_DOWN]:
                self.achievements_scroll_offset = min(max_scroll, self.achievements_scroll_offset + 5)
        
        # Рисуем достижения напрямую на экран с клиппингом
        clip_rect = pygame.Rect(container_x + 2, container_y + 2, container_w - 4, container_h - 4)
        screen.set_clip(clip_rect)

        y_screen = container_y + 20 - self.achievements_scroll_offset
        
        for ach_id, achievement in achievements_list:
            is_unlocked = self.save_system.data["achievements"].get(ach_id, False)
            
        # Рисуем достижения напрямую на экран с клиппингом
        clip_rect = pygame.Rect(container_x + 2, container_y + 2, container_w - 4, container_h - 4)
        screen.set_clip(clip_rect)

        y_screen = container_y + 20 - self.achievements_scroll_offset

        for ach_id, achievement in achievements_list:
            is_unlocked = self.save_system.data["achievements"].get(ach_id, False)
            
            # Пропускаем, если карточка за пределами видимости
            if y_screen + card_height < container_y or y_screen > container_y + container_h:
                y_screen += card_height + spacing
                continue
            
            # Карточка достижения
            card_rect = pygame.Rect(container_x + 10, y_screen, container_w - 30, card_height)
            card_color = (40, 50, 60) if is_unlocked else (25, 30, 40)
            pygame.draw.rect(screen, card_color, card_rect, border_radius=10)
            border_color = COLORS["player"] if is_unlocked else (60, 70, 90)
            pygame.draw.rect(screen, border_color, card_rect, 2, border_radius=10)
            
            # Название и описание
            name_text = self.font_small.render(achievement.name, True, COLORS["player"] if is_unlocked else (150, 150, 170))
            screen.blit(name_text, (card_rect.x + 20, card_rect.y + 15))
            
            desc_text = self.font_tiny.render(achievement.description, True, (180, 180, 200))
            screen.blit(desc_text, (card_rect.x + 20, card_rect.y + 48))
            
            # Награда
            reward_text = self.font_tiny.render(f"+{achievement.reward} валюты", True, COLORS["warning"])
            screen.blit(reward_text, (card_rect.right - 160, card_rect.y + 15))
            
            # Кнопка получения награды
            if is_unlocked:
                is_claimed = self.save_system.data.get("achievement_rewards_claimed", {}).get(achievement.id, False)
                
                if not is_claimed:
                    button_w, button_h = 120, 35
                    button_rect = pygame.Rect(card_rect.right - button_w - 15, card_rect.bottom - button_h - 8, button_w, button_h)
                    
                    # Прямая проверка позиции мыши на экране
                    button_hover = button_rect.collidepoint(mouse_pos) and clip_rect.collidepoint(mouse_pos)
                    
                    button_color = (60, 140, 60) if button_hover else (40, 100, 40)
                    pygame.draw.rect(screen, button_color, button_rect, border_radius=8)
                    pygame.draw.rect(screen, COLORS["warning"], button_rect, 2, border_radius=8)
                    
                    btn_text = self.font_tiny.render("ПОЛУЧИТЬ", True, COLORS["warning"])
                    screen.blit(btn_text, btn_text.get_rect(center=button_rect.center))
                    
                    if button_hover and pygame.mouse.get_pressed()[0]:
                        claimed_key = f"_ach_click_{achievement.id}"
                        if not getattr(self, claimed_key, False):
                            setattr(self, claimed_key, True)
                            self.save_system.data["currency"] += achievement.reward
                            if "achievement_rewards_claimed" not in self.save_system.data:
                                self.save_system.data["achievement_rewards_claimed"] = {}
                            self.save_system.data["achievement_rewards_claimed"][achievement.id] = True
                            self.save_system.save()
                            self.sound_manager.play_sound("powerup")
                            pygame.time.delay(150)
                else:
                    claimed_text = self.font_tiny.render("[✓] ПОЛУЧЕНО", True, (100, 180, 100))
                    screen.blit(claimed_text, (card_rect.right - 150, card_rect.bottom - 28))
            
            # Прогресс-бар если не выполнено
            if not is_unlocked:
                try:
                    progress = achievement.get_progress(self)
                    bar_w = 120
                    bar_x = card_rect.right - 320
                    bar_y = card_rect.y + 38
                    pygame.draw.rect(screen, (40, 40, 50), (bar_x, bar_y, bar_w, 18), border_radius=9)
                    progress_w = int(bar_w * progress)
                    if progress_w > 0:
                        pygame.draw.rect(screen, COLORS["exp"], (bar_x, bar_y, progress_w, 18), border_radius=9)
                    percent_text = self.font_tiny.render(f"{int(progress*100)}%", True, COLORS["ui"])
                    screen.blit(percent_text, (bar_x + bar_w + 10, bar_y))
                except:
                    pass
            
            y_screen += card_height + spacing
        
        screen.set_clip(None)
        
        # Полоса прокрутки
        if max_scroll > 0:
            scrollbar_height = max(40, int((container_h / total_content_height) * container_h))
            scroll_ratio = self.achievements_scroll_offset / max_scroll
            scrollbar_y = container_y + int(scroll_ratio * (container_h - scrollbar_height))
            scrollbar_y = max(container_y, min(container_y + container_h - scrollbar_height, scrollbar_y))
            scrollbar_rect = pygame.Rect(container_x + container_w - 15, scrollbar_y, 10, scrollbar_height)
            pygame.draw.rect(screen, COLORS["player"], scrollbar_rect, border_radius=5)
        
        # Подсказка о прокрутке
        hint_text = self.font_tiny.render("Колесо мыши или стрелки для прокрутки", True, (120, 120, 140))
        screen.blit(hint_text, (WIDTH // 2 - hint_text.get_width() // 2, HEIGHT - 130))
        
        self.draw_back_button()
    

    def draw_knowledge_menu(self):
        """База знаний - вкладки Враги и Перки"""
        # Инициализация состояния
        if not hasattr(self, 'knowledge_tab'):
            self.knowledge_tab = "enemies"
        if not hasattr(self, 'knowledge_scroll'):
            self.knowledge_scroll = 0
        
        # Фон
        for i in range(HEIGHT):
            p = i / HEIGHT
            pygame.draw.line(screen, (int(5+15*p), int(8+20*p), int(18+35*p)), (0,i),(WIDTH,i))
        
        # Заголовок
        title = self.font_large.render("БАЗА ЗНАНИЙ", True, COLORS["player"])
        screen.blit(title, title.get_rect(center=(WIDTH//2, 55)))
        
        # Вкладки (добавлена вкладка СПОСОБНОСТИ)
        tab_w, tab_h = 200, 50
        tab_y = 100
        tabs = [("enemies", "ВРАГИ"), ("perks", "ПЕРКИ"), ("abilities", "СПОСОБНОСТИ")]
        num_tabs = len(tabs)
        tab_total_w = num_tabs * tab_w + (num_tabs - 1) * 15
        tab_start_x = WIDTH // 2 - tab_total_w // 2
        tab_rects = {}
        for idx, (tid, tlabel) in enumerate(tabs):
            tx = tab_start_x + idx * (tab_w + 15)
            trect = pygame.Rect(tx, tab_y, tab_w, tab_h)
            tab_rects[tid] = trect
            is_active = self.knowledge_tab == tid
            bg = (50, 60, 80) if is_active else (30, 35, 50)
            border = COLORS["player"] if is_active else COLORS["card_border"]
            bw = 3 if is_active else 1
            pygame.draw.rect(screen, bg, trect, border_radius=10)
            pygame.draw.rect(screen, border, trect, bw, border_radius=10)
            tab_txt = self.font_small.render(tlabel, True, COLORS["player"] if is_active else (150,155,175))
            screen.blit(tab_txt, tab_txt.get_rect(center=trect.center))
            mouse_pos = pygame.mouse.get_pos()
            if trect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0]:
                if self.knowledge_tab != tid:
                    self.knowledge_tab = tid
                    self.knowledge_scroll = 0
        
        # Контейнер
        cont_x = WIDTH//2 - self.CONTAINER_W//2
        cont_y = 170
        cont_w = self.CONTAINER_W
        cont_h = HEIGHT - 290
        cont_rect = pygame.Rect(cont_x, cont_y, cont_w, cont_h)
        pygame.draw.rect(screen, (15, 18, 25), cont_rect, border_radius=12)
        pygame.draw.rect(screen, COLORS["card_border"], cont_rect, 2, border_radius=12)
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Keyboard scroll
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.knowledge_scroll = max(0, self.knowledge_scroll - 5)
        if keys[pygame.K_DOWN]:
            self.knowledge_scroll += 5
        
        if self.knowledge_tab == "enemies":
            enemies_data = [
                {"name": "ДРОН", "color": COLORS["enemy"], "shape": "circle",
                 "desc": "Стандартный враг фракции Рой. Движется прямо к игроку. Особенность: при смерти на высоких рангах ускоряет ближних союзников.",
                 "stats": "HP: 30  Урон: 8  Скорость: 2.5  Опыт: 10  Ранг: 1"},
                {"name": "СТРЕМИТЕЛЬНЫЙ", "color": (255, 200, 40), "shape": "triangle",
                 "desc": "Быстрый враг фракции Рой. Опасен в группах. Особенность: при низком HP (25%) резко меняет направление движения.",
                 "stats": "HP: 20  Урон: 5  Скорость: 5.0  Опыт: 15  Ранг: 1"},
                {"name": "БРОНЕТАНК", "color": COLORS["elite_enemy"], "shape": "square",
                 "desc": "Тяжёлый враг фракции Элита. Медленный, но прочный. Особенность: броня снижает весь получаемый урон на 20%.",
                 "stats": "HP: 100  Урон: 10  Скорость: 1.5  Опыт: 30  Броня: 20%"},
                {"name": "ПОВЕЛИТЕЛЬ", "color": COLORS["boss"], "shape": "hexagon",
                 "desc": "Боссовый враг фракции Командиры. Огромный HP, высокий урон. Особенность: периодически призывает рой союзников.",
                 "stats": "HP: 500  Урон: 18  Скорость: 2.0  Опыт: 200"},
                {"name": "ОХОТНИК", "color": (180, 40, 220), "shape": "diamond",
                 "desc": "Дальнобойный снайпер фракции Теневые. Стреляет быстрыми прицельными снарядами с упреждением. Особенность: на высоких рангах пуля пробивает неуязвимость игрока.",
                 "stats": "HP: 45  Урон: 18  Скорость: 1.2  Опыт: 25  Дальность: 700px"},
                {"name": "ЛИЧИНКА", "color": (255, 120, 30), "shape": "circle",
                 "desc": "Крошечный враг фракции Рой. Очень слабый по одиночке, смертоносен в больших роях. Высокая скорость.",
                 "stats": "HP: 12  Урон: 3  Скорость: 6.5  Опыт: 8"},
                {"name": "ФАНТОМ", "color": (140, 50, 200), "shape": "hexagon",
                 "desc": "Призрак фракции Теневые. Особенность: каждые 3 секунды входит в фазу неуязвимости на 0.8с — пули проходят насквозь. Ждите окончания фазы.",
                 "stats": "HP: 35  Урон: 12  Скорость: 3.5  Опыт: 20  Фаза: 0.8с"},
                {"name": "БЕРСЕРК", "color": (60, 160, 240), "shape": "square",
                 "desc": "Тяжёлый враг фракции Элита. Особенность: при падении HP ниже 40% впадает в берсерк — скорость x1.8, урон x1.5. Добивайте быстро!",
                 "stats": "HP: 160  Урон: 15  Скорость: 2.2 (до 4.0)  Опыт: 45"},
                {"name": "ПАРАЗИТ", "color": (220, 50, 200), "shape": "triangle",
                 "desc": "Живучий враг фракции Теневые. Особенность: при каждом ударе по игроку восстанавливает своё HP. Чем дольше контакт — тем опаснее.",
                 "stats": "HP: 55  Урон: 7  Скорость: 3.0  Опыт: 20  Лечение: 8+/удар"},
                {"name": "КАМИКАДЗЕ", "color": (255, 80, 20), "shape": "circle",
                 "desc": "Взрывной враг фракции Рой. Особенность: при смерти создаёт взрыв в радиусе 80px. Никогда не добивайте вблизи — отступите и расстреляйте издалека.",
                 "stats": "HP: 50  Урон касания: 25  Взрыв: 40 AOE  Скорость: 1.8  Опыт: 35"},
                {"name": "РЕЙНДЖЕР", "color": (60, 200, 220), "shape": "diamond",
                 "desc": "Дальнобойный враг фракции Элита. Держится на дистанции 350px, стреляет тройными выстрелами на высоких рангах. Атакует с упреждением.",
                 "stats": "HP: 50  Урон: 16  Скорость: 1.5  Опыт: 30  Дальность: 350px"},
                {"name": "МОРТИРЩИК", "color": (180, 100, 40), "shape": "square",
                 "desc": "Осадный враг фракции Командиры. Особенность: стреляет медленными снарядами, которые взрываются в точке прицеливания по истечении времени. Следите за прицелом!",
                 "stats": "HP: 70  Урон взрыва: 22 AOE  Скорость: 0.6  Опыт: 40"},
                {"name": "ЩИТОНОСЕЦ", "color": (80, 200, 255), "shape": "hexagon",
                 "desc": "Поддержка фракции Командиры. Стремится держаться рядом со своими союзниками. Особенность: каждые 1.5с наделяет союзников в ауре 200px временным щитом. Имеет собственный щит. Убейте первым!",
                 "stats": "HP: 200  Урон: 8  Скорость: 1.0  Опыт: 60  Аура: 200px"},
                {"name": "ЧАСОВОЙ", "color": (60, 120, 255), "shape": "hexagon",
                 "desc": "Элитный враг фракции Командиры. Огромный HP и мощный урон. Особенность: при ударе создаёт волну отталкивания — игрок отлетает назад.",
                 "stats": "HP: 280  Урон: 20  Скорость: 0.7  Опыт: 80"},
                {"name": "ЛАНЦЕТ", "color": (80, 220, 180), "shape": "triangle",
                 "desc": "Дальнобойный враг фракции Элита. Особенность: стреляет пробивающими снарядами, которые проходят сквозь нескольких врагов. Держится на дистанции 400px.",
                 "stats": "HP: 40  Урон: 12  Скорость: 2.0  Опыт: 28  Пробитие: +1"},
                {"name": "РЕГЕНЕРАТОР", "color": (50, 220, 100), "shape": "circle",
                 "desc": "Лечащая поддержка фракции Поддержка. Старается находиться рядом с союзниками. Особенность: каждые 2с восстанавливает HP всем союзникам в ауре 200px. Приоритетная цель!",
                 "stats": "HP: 65  Урон: 6  Скорость: 1.8  Опыт: 50  Лечение: 8/2с"},
                {"name": "УСИЛИТЕЛЬ", "color": (220, 200, 50), "shape": "diamond",
                 "desc": "Усиляющая поддержка фракции Поддержка. Держится рядом с союзниками. Особенность: каждые 3с даёт всем союзникам в ауре 180px +40% скорость и урон на 2с.",
                 "stats": "HP: 55  Урон: 5  Скорость: 1.5  Опыт: 55  Бафф: +40% скорость/урон"},
            ]
            card_h = 125
            spacing = 14
            total_h = len(enemies_data) * (card_h + spacing)
            max_scroll = max(0, total_h - cont_h + 30)
            self.knowledge_scroll = max(0, min(max_scroll, self.knowledge_scroll))
            
            screen.set_clip(pygame.Rect(cont_x+2, cont_y+2, cont_w-4, cont_h-4))
            y = cont_y + 15 - self.knowledge_scroll
            for ed in enemies_data:
                if y + card_h > cont_y and y < cont_y + cont_h:
                    cr = pygame.Rect(cont_x + 15, y, cont_w - 30, card_h)
                    pygame.draw.rect(screen, (28, 32, 48), cr, border_radius=10)
                    pygame.draw.rect(screen, ed["color"], cr, 2, border_radius=10)
                    
                    # Shape preview
                    px, py = cr.x + 55, cr.y + card_h//2
                    sz = 20
                    c = ed["color"]
                    s = ed["shape"]
                    if s == "circle": pygame.draw.circle(screen, c, (px, py), sz)
                    elif s == "square": pygame.draw.rect(screen, c, (px-sz, py-sz, sz*2, sz*2))
                    elif s == "triangle":
                        pts2 = [(px,py-sz),(px-sz,py+sz),(px+sz,py+sz)]
                        pygame.draw.polygon(screen, c, pts2)
                    elif s == "hexagon":
                        pts2 = [(int(px+sz*math.cos(math.radians(60*i+30))), int(py+sz*math.sin(math.radians(60*i+30)))) for i in range(6)]
                        pygame.draw.polygon(screen, c, pts2)
                    elif s == "diamond":
                        pts2 = [(px,py-sz),(px+sz,py),(px,py+sz),(px-sz,py)]
                        pygame.draw.polygon(screen, c, pts2)
                    
                    # Text
                    name_t = self.font_small.render(ed["name"], True, ed["color"])
                    screen.blit(name_t, (cr.x + 110, cr.y + 10))
                    # Description - split into lines of ~85 chars
                    desc_full = ed["desc"]
                    desc_lines = []
                    words = desc_full.split()
                    line = ""
                    for w in words:
                        test = line + " " + w if line else w
                        if self.font_tiny.size(test)[0] < cont_w - 160:
                            line = test
                        else:
                            desc_lines.append(line)
                            line = w
                    if line:
                        desc_lines.append(line)
                    for li, dl in enumerate(desc_lines[:3]):
                        desc_t = self.font_tiny.render(dl, True, (180,180,200))
                        screen.blit(desc_t, (cr.x + 110, cr.y + 42 + li * 20))
                    stats_t = self.font_tiny.render(ed["stats"], True, COLORS["warning"])
                    screen.blit(stats_t, (cr.x + 110, cr.y + 100))
                y += card_h + spacing
            screen.set_clip(None)
            
            # Scrollbar
            if max_scroll > 0:
                sb_h = max(30, int((cont_h / total_h) * cont_h))
                sb_y = cont_y + int((self.knowledge_scroll / max_scroll) * (cont_h - sb_h))
                pygame.draw.rect(screen, COLORS["player"], (cont_x + cont_w - 12, sb_y, 8, sb_h), border_radius=4)
        
        elif self.knowledge_tab == "abilities":
            # ---- ВКЛАДКА СПОСОБНОСТЕЙ ----
            KB_ABILITIES = [
                {"id": "dash_boost",   "name": "РЫВОК-УДАР",        "color": COLORS["player"],
                 "key": "Q",  "cd": "Пассивный",
                 "icon": "[>>]",
                 "desc": "Каждый рывок наносит 30 урона всем врагам на его пути. Эффект постоянный — срабатывает автоматически при каждом рывке."},
                {"id": "shield_pulse", "name": "ИМПУЛЬС ЩИТА",      "color": COLORS["shield"],
                 "key": "Q",  "cd": "6с",
                 "icon": "[()]",
                 "desc": "Создаёт мощный импульс энергии вокруг вас — все враги в радиусе 250px мгновенно отбрасываются. Отличен для побега из окружения."},
                {"id": "time_slow",    "name": "ЗАМЕДЛЕНИЕ",         "color": (100, 200, 255),
                 "key": "Q",  "cd": "12с",
                 "icon": "[<<]",
                 "desc": "Замедляет всех текущих врагов на поле на 60% скорости в течение 4 секунд. Замедлённые враги светятся синим. Не замораживает, но даёт время перегруппироваться."},
                {"id": "overdrive",    "name": "ПЕРЕГРУЗКА",         "color": COLORS["warning"],
                 "key": "Q",  "cd": "15с",
                 "icon": "[!!]",
                 "desc": "Удваивает скорострельность на 5 секунд. В сочетании с мультивыстрелом или взрывными пулями урон возрастает многократно. Эффект виден по золотому свечению."},
                {"id": "nuke",         "name": "ЯДЕРНЫЙ ЗАРЯД",     "color": COLORS["enemy"],
                 "key": "Q",  "cd": "20с",
                 "icon": "[*]",
                 "desc": "Мощнейший взрыв в радиусе 400px наносит 150 единиц урона всем врагам в зоне. Мгновенно убивает большинство рядовых врагов. Долгая перезарядка."},
                {"id": "heal_pulse",   "name": "ПУЛЬС ИСЦЕЛЕНИЯ",   "color": (100, 255, 150),
                 "key": "Q",  "cd": "18с",
                 "icon": "[+]",
                 "desc": "Восстанавливает 40% от максимального HP и добавляет 80 единиц щита на 3 секунды. Незаменима при критически низком здоровье."},
                {"id": "bullet_storm", "name": "ШТОРМ ПУЛЬ",        "color": (255, 180, 50),
                 "key": "Q",  "cd": "10с",
                 "icon": "[x]",
                 "desc": "Единовременно выпускает 24 пули равномерно во всех направлениях. Каждая пуля — полноценный выстрел с вашими характеристиками крита и урона."},
            ]
            card_h = 100
            spacing = 14
            total_h = len(KB_ABILITIES) * (card_h + spacing)
            max_scroll = max(0, total_h - cont_h + 30)
            self.knowledge_scroll = max(0, min(max_scroll, self.knowledge_scroll))
            
            owned_abs = self.save_system.data.get("owned_abilities", [])
            active_ab = self.save_system.data.get("active_ability", "")
            
            screen.set_clip(pygame.Rect(cont_x+2, cont_y+2, cont_w-4, cont_h-4))
            y = cont_y + 15 - self.knowledge_scroll
            for ab in KB_ABILITIES:
                if y + card_h > cont_y and y < cont_y + cont_h:
                    is_owned = ab["id"] in owned_abs
                    is_act = ab["id"] == active_ab
                    cr = pygame.Rect(cont_x + 15, y, cont_w - 30, card_h)
                    cb = (50, 65, 80) if is_act else ((35, 44, 58) if is_owned else (22, 26, 38))
                    pygame.draw.rect(screen, cb, cr, border_radius=10)
                    pygame.draw.rect(screen, ab["color"] if is_owned else (55, 60, 75), cr, 3 if is_act else 2, border_radius=10)
                    # Icon
                    ic = self.font_medium.render(ab["icon"], True, ab["color"] if is_owned else (80,80,95))
                    screen.blit(ic, (cr.x + 15, cr.y + card_h//2 - ic.get_height()//2))
                    # Key badge
                    if is_owned:
                        kb_r = pygame.Rect(cr.x + 70, cr.y + card_h//2 - 20, 36, 40)
                        pygame.draw.rect(screen, (35,45,60), kb_r, border_radius=8)
                        pygame.draw.rect(screen, ab["color"], kb_r, 2, border_radius=8)
                        kt = self.font_small.render("Q", True, ab["color"])
                        screen.blit(kt, kt.get_rect(center=kb_r.center))
                    # Name + status
                    nc = ab["color"] if is_owned else (120,125,140)
                    tx = cr.x + 120 if is_owned else cr.x + 80
                    screen.blit(self.font_small.render(ab["name"], True, nc), (tx, cr.y + 12))
                    screen.blit(self.font_tiny.render(f"КД: {ab['cd']}", True, (150,160,180) if is_owned else (80,85,95)), (tx, cr.y + 42))
                    screen.blit(self.font_tiny.render(ab["desc"], True, (170,175,195) if is_owned else (90,95,110)), (tx, cr.y + 65))
                    # Status badge
                    if is_act:
                        act_badge = self.font_tiny.render("[АКТИВНА]", True, ab["color"])
                        screen.blit(act_badge, (cr.right - act_badge.get_width() - 15, cr.y + 12))
                    elif not is_owned:
                        lock_t = self.font_tiny.render("[НЕ КУПЛЕНА]", True, (100,100,115))
                        screen.blit(lock_t, (cr.right - lock_t.get_width() - 15, cr.y + 12))
                y += card_h + spacing
            screen.set_clip(None)
            
            if max_scroll > 0:
                sb_h = max(30, int((cont_h / total_h) * cont_h))
                sb_y = cont_y + int((self.knowledge_scroll / max_scroll) * (cont_h - sb_h))
                pygame.draw.rect(screen, COLORS["player"], (cont_x + cont_w - 12, sb_y, 8, sb_h), border_radius=4)
        
        else:  # perks tab
            perks_data = [
                ("+HP / +HP БОЛЬШОЙ", "common/uncommon", "Увеличивает максимальное здоровье. Берите для выживаемости."),
                ("+УРОН / +УРОН БОЛЬШОЙ", "common/uncommon", "Прямое увеличение урона всех пуль. Ключевой перк для ДПС."),
                ("СКОРОСТРЕЛЬНОСТЬ", "common/rare", "Уменьшает задержку между выстрелами. Минимум 50мс задержки."),
                ("СКОРОСТЬ", "common/uncommon", "Увеличивает скорость передвижения. Максимум 5 стаков."),
                ("КРИТ ШАНС / КРИТ УРОН", "uncommon/epic", "Критические удары наносят 2x+ урона. Работают вместе."),
                ("МУЛЬТИВЫСТРЕЛ", "rare/epic", "Стреляете несколькими пулями в разные стороны. Макс 6 пуль."),
                ("ДВОЙНОЙ ВЫСТРЕЛ", "uncommon", "Дополнительные пули летят вслед за основной (--|). Макс 3 стека."),
                ("ПРОБИТИЕ", "uncommon/rare", "Пули проходят сквозь врагов не исчезая."),
                ("ЩИТ", "common/uncommon", "Дополнительный барьер HP, поглощает урон вместо здоровья."),
                ("ВАМПИРИЗМ", "uncommon/rare", "Восстанавливает HP за каждый нанесённый урон. Макс 75%."),
                ("РЕГЕНЕРАЦИЯ", "rare", "Постепенно восстанавливает HP каждую секунду."),
                ("БРОНЯ", "epic", "Снижает весь получаемый урон. Макс 60%. Одноразовый перк."),
                ("ОРБИТАЛЬНАЯ ЗАЩИТА", "legendary", "Снаряды вращаются вокруг вас, поражая ближних врагов."),
                ("ВЗРЫВНЫЕ ПУЛИ", "legendary", "Каждое попадание вызывает взрыв вокруг врага."),
                ("ЗАМОРАЖИВАНИЕ", "legendary", "Пули замедляют врагов вдвое на несколько секунд."),
                ("ЯД", "legendary", "Пули наносят 15 урона в секунду в течение 3 секунд."),
                ("ЦЕПНАЯ МОЛНИЯ", "legendary", "Урон перепрыгивает на ближних врагов вокруг цели."),
                ("ОТРАЖЕНИЕ", "legendary", "Отражает 25% получаемого урона обратно во врага."),
                ("ШИПЫ", "legendary", "Враги получают 10 урона при каждой атаке на вас."),
                ("ПОЛНОЕ ВОССТАНОВЛЕНИЕ", "epic", "Одноразовый: немедленно восстанавливает всё HP и щит."),
            ]
            card_h = 85
            spacing = 12
            total_h = len(perks_data) * (card_h + spacing)
            max_scroll = max(0, total_h - cont_h + 30)
            self.knowledge_scroll = max(0, min(max_scroll, self.knowledge_scroll))
            
            rarity_color_map = {
                "common": (200,200,200), "uncommon": (100,255,100), "rare": (100,150,255),
                "epic": (200,100,255), "legendary": (255,200,0)
            }
            
            screen.set_clip(pygame.Rect(cont_x+2, cont_y+2, cont_w-4, cont_h-4))
            y = cont_y + 15 - self.knowledge_scroll
            for (pname, prarity, pdesc) in perks_data:
                if y + card_h > cont_y and y < cont_y + cont_h:
                    # Get color from first rarity mentioned
                    first_rar = prarity.split("/")[0].strip()
                    rcol = rarity_color_map.get(first_rar, (180,180,180))
                    cr = pygame.Rect(cont_x + 15, y, cont_w - 30, card_h)
                    pygame.draw.rect(screen, (28, 32, 48), cr, border_radius=10)
                    pygame.draw.rect(screen, rcol, cr, 2, border_radius=10)
                    
                    # Rarity badge (inside card, top right)
                    rar_t = self.font_tiny.render(prarity.upper(), True, rcol)
                    rar_bg = pygame.Rect(cr.right - rar_t.get_width() - 22, cr.y + 6, rar_t.get_width() + 14, 20)
                    pygame.draw.rect(screen, (20,22,38), rar_bg, border_radius=5)
                    pygame.draw.rect(screen, rcol, rar_bg, 1, border_radius=5)
                    screen.blit(rar_t, (rar_bg.x + 7, rar_bg.y + 1))
                    
                    name_t = self.font_small.render(pname, True, COLORS["ui"])
                    screen.blit(name_t, (cr.x + 20, cr.y + 14))
                    desc_t = self.font_tiny.render(pdesc[:95], True, (180,180,200))
                    screen.blit(desc_t, (cr.x + 20, cr.y + 48))
                    if len(pdesc) > 95:
                        desc2_t = self.font_tiny.render(pdesc[95:], True, (180,180,200))
                        screen.blit(desc2_t, (cr.x + 20, cr.y + 66))
                y += card_h + spacing
            screen.set_clip(None)
            
            if max_scroll > 0:
                sb_h = max(30, int((cont_h / total_h) * cont_h))
                sb_y = cont_y + int((self.knowledge_scroll / max_scroll) * (cont_h - sb_h))
                pygame.draw.rect(screen, COLORS["player"], (cont_x + cont_w - 12, sb_y, 8, sb_h), border_radius=4)
        
        # Hint
        hint_t = self.font_tiny.render("Колесико мыши или стрелки для прокрутки", True, (120,120,140))
        screen.blit(hint_t, hint_t.get_rect(center=(WIDTH//2, HEIGHT - 110)))
        
        self.draw_back_button()

    def draw_back_button(self):
        button_rect = pygame.Rect(50, HEIGHT - 100, 200, 60)
        mouse_pos = pygame.mouse.get_pos()
        is_hover = button_rect.collidepoint(mouse_pos)
        
        color = COLORS["player"] if is_hover else COLORS["card_border"]
        pygame.draw.rect(screen, color, button_rect, 3, border_radius=8)
        
        text = self.font_small.render("НАЗАД", True, COLORS["player"])
        text_rect = text.get_rect(center=button_rect.center)
        screen.blit(text, text_rect)
        
        if is_hover and pygame.mouse.get_pressed()[0]:
            self.menu_page = "main"
            pygame.time.delay(200)
    
    def draw_level_up(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        title = self.font_huge.render("ПОВЫШЕНИЕ УРОВНЯ!", True, COLORS["player"])
        title_rect = title.get_rect(center=(WIDTH // 2, 150))
        screen.blit(title, title_rect)
        
        subtitle = self.font_medium.render(f"Уровень {self.player.level}", True, COLORS["ui"])
        subtitle_rect = subtitle.get_rect(center=(WIDTH // 2, 230))
        screen.blit(subtitle, subtitle_rect)
        
        if not hasattr(self, 'current_perks'):
            self.current_perks = PerkManager.get_available_perks(self.player)
        
        card_width, card_height = 350, 200
        total_width = len(self.current_perks) * card_width + (len(self.current_perks) - 1) * 40
        start_x = (WIDTH - total_width) // 2
        card_y = HEIGHT // 2 - card_height // 2
        
        mouse_pos = pygame.mouse.get_pos()
        # Выбираем перк только если кнопка была отпущена ПОСЛЕ появления экрана
        # (level_up_click_handled == False означает что со времени открытия экрана кнопку отпускали)
        can_select = not self.level_up_click_handled
        
        for i, perk in enumerate(self.current_perks):
            card_x = start_x + i * (card_width + 40)
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            
            is_hover = card_rect.collidepoint(mouse_pos)
            
            rarity_color = RARITY_COLORS.get(perk.rarity, COLORS["card_border"])
            
            card_color = COLORS["card"] if not is_hover else (40, 45, 65)
            pygame.draw.rect(screen, card_color, card_rect, border_radius=15)
            
            # Свечение для редких перков
            if perk.rarity in ["epic", "legendary"]:
                glow_rect = card_rect.inflate(8, 8)
                glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
                glow_alpha = 40 if perk.rarity == "epic" else 60
                pygame.draw.rect(glow_surf, (*rarity_color, glow_alpha), glow_surf.get_rect(), border_radius=17)
                screen.blit(glow_surf, glow_rect)
            
            border_width = 5 if is_hover else 3
            pygame.draw.rect(screen, rarity_color, card_rect, border_width, border_radius=15)
            
            # Плашка редкости сверху карточки
            rarity_names = {
                "common": "ОБЫЧНЫЙ", "uncommon": "НЕОБЫЧНЫЙ",
                "rare": "РЕДКИЙ", "epic": "ЭПИЧЕСКИЙ", "legendary": "ЛЕГЕНДАРНЫЙ"
            }
            rarity_label = self.font_tiny.render(rarity_names.get(perk.rarity, ""), True, rarity_color)
            rarity_bg = pygame.Rect(card_rect.x + 8, card_rect.y - 14, rarity_label.get_width() + 16, 22)
            pygame.draw.rect(screen, (20, 22, 38), rarity_bg, border_radius=5)
            pygame.draw.rect(screen, rarity_color, rarity_bg, 1, border_radius=5)
            screen.blit(rarity_label, (rarity_bg.x + 8, rarity_bg.y + 1))  # +1 вместо +3
            
            icon_text = self.font_large.render(perk.icon, True, rarity_color)
            icon_rect = icon_text.get_rect(center=(card_rect.centerx, card_rect.y + 48))
            screen.blit(icon_text, icon_rect)
            
            name_text = self.font_small.render(perk.name, True, COLORS["ui"])
            name_rect = name_text.get_rect(center=(card_rect.centerx, card_rect.y + 105))
            screen.blit(name_text, name_rect)
            
            words = perk.description.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if self.font_tiny.size(test_line)[0] < card_width - 20:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            desc_y = card_rect.y + 135
            for line in lines[:2]:
                desc_text = self.font_tiny.render(line, True, (180, 180, 200))
                desc_rect = desc_text.get_rect(center=(card_rect.centerx, desc_y))
                screen.blit(desc_text, desc_rect)
                desc_y += 22
            
            # Подсказка "НАЖМИТЕ" если можно выбрать, иначе "ОТПУСТИТЕ КНОПКУ"
            if is_hover:
                if can_select:
                    hint = self.font_tiny.render("НАЖМИТЕ ДЛЯ ВЫБОРА", True, rarity_color)
                    pygame.draw.rect(screen, (20, 22, 38),
                                     pygame.Rect(card_rect.x, card_rect.bottom - 28, card_rect.width, 28),
                                     border_radius=12)
                else:
                    hint = self.font_tiny.render("ОТПУСТИТЕ КНОПКУ МЫШИ", True, (180, 180, 200))
                    pygame.draw.rect(screen, (30, 30, 30),
                                     pygame.Rect(card_rect.x, card_rect.bottom - 28, card_rect.width, 28),
                                     border_radius=12)
                hint_rect = hint.get_rect(center=(card_rect.centerx, card_rect.bottom - 14))
                screen.blit(hint, hint_rect)
            
            # Выбор только если кнопка была предварительно отпущена
            if is_hover and can_select and pygame.mouse.get_pressed()[0]:
                self.level_up_click_handled = True
                PerkManager.apply_perk(self.player, perk.id)
                delattr(self, 'current_perks')
                self.state = GameState.PLAY
                self.sound_manager.play_sound("powerup")
                return

    def draw_wave_complete(self):
        # Просто показываем таймер вверху экрана
        timer_text = self.font_large.render(
            f"Следующая волна через: {int(self.wave_system.wave_break_time)}s",
            True, COLORS["warning"]
        )
        timer_rect = timer_text.get_rect(center=(WIDTH // 2, 60))
        
        # Полупрозрачный фон для текста
        bg_rect = pygame.Rect(timer_rect.x - 20, timer_rect.y - 10, 
                              timer_rect.width + 40, timer_rect.height + 20)
        pygame.draw.rect(screen, (0, 0, 0, 200), bg_rect, border_radius=10)
        pygame.draw.rect(screen, COLORS["warning"], bg_rect, 3, border_radius=10)
        
        screen.blit(timer_text, timer_rect)
    
    def draw_pause(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 15, 180))
        screen.blit(overlay, (0, 0))
        
        pause_text = self.font_huge.render("ПАУЗА", True, COLORS["ui"])
        pause_rect = pause_text.get_rect(center=(WIDTH // 2, 80))
        screen.blit(pause_text, pause_rect)
        
        # Собираем список активных перков
        upgrade_texts = []
        p = self.player
        if p.upgrades["max_hp"] > 0:
            upgrade_texts.append(f"[HP] +{p.upgrades['max_hp'] * 25} HP")
        if p.upgrades["dmg"] > 0:
            upgrade_texts.append(f"[URN] +{p.upgrades['dmg'] * 5} урона")
        if p.upgrades["fire_rate"] > 0:
            upgrade_texts.append(f"[ATK] +{p.upgrades['fire_rate'] * 15}% скорострел.")
        if p.upgrades["speed"] > 0:
            upgrade_texts.append(f"[SPD] +{p.upgrades['speed'] * 10}% скорости")
        if p.upgrades["crit_chance"] > 0:
            upgrade_texts.append(f"[CRT] +{p.upgrades['crit_chance'] * 5}% крит")
        if p.upgrades["multishot"] > 0:
            upgrade_texts.append(f"[PUL] {p.multishot} пуль")
        if p.upgrades["piercing"] > 0:
            upgrade_texts.append(f"[PRB] Пробитие {p.piercing}")
        if p.upgrades["lifesteal"] > 0:
            upgrade_texts.append(f"[VAM] {int(p.lifesteal * 100)}% вампиризм")
        if p.upgrades["shield"] > 0:
            upgrade_texts.append(f"[SHD] +{p.upgrades['shield'] * 50} щита")
        
        # Специальные способности
        if hasattr(p, 'regen') and p.regen > 0:
            upgrade_texts.append(f"[REG] {p.regen} HP/сек")
        if hasattr(p, 'armor') and p.armor > 0:
            upgrade_texts.append(f"[ARM] {int(p.armor * 100)}% брони")
        if hasattr(p, 'exp_magnet_mult') and p.exp_magnet_mult > 1:
            upgrade_texts.append(f"[MAG] +{int((p.exp_magnet_mult - 1) * 100)}% магнит")
        if hasattr(p, 'orbital_bullets'):
            upgrade_texts.append("[ORB] Орбита")
        if hasattr(p, 'explosive_bullets'):
            upgrade_texts.append("[EXP] Взрывы")
        if hasattr(p, 'freeze_bullets'):
            upgrade_texts.append("[ICE] Заморозка")
        if hasattr(p, 'poison_bullets'):
            upgrade_texts.append("[PSN] Яд")
        if hasattr(p, 'chain_lightning'):
            upgrade_texts.append("[MLN] Молния")
        if hasattr(p, 'reflect_damage') and p.reflect_damage > 0:
            upgrade_texts.append(f"[REF] {int(p.reflect_damage * 100)}% отраж.")
        if hasattr(p, 'thorns') and p.thorns > 0:
            upgrade_texts.append(f"[SHP] {p.thorns} шипов")
        if p.crit_multiplier > 2.0:
            upgrade_texts.append(f"[CDM] x{p.crit_multiplier:.1f} крит")
        if p.bullet_size > 1.0:
            upgrade_texts.append(f"[SIZ] +{int((p.bullet_size - 1) * 100)}% размер")
        
        if not upgrade_texts:
            upgrade_texts = ["Пока нет улучшений"]
        
        # Отрисовка в 2 колонки ПО ЦЕНТРУ экрана
        upgrades_title = self.font_small.render("АКТИВНЫЕ ПЕРКИ:", True, COLORS["player"])
        title_x = WIDTH // 2 - upgrades_title.get_width() // 2
        screen.blit(upgrades_title, (title_x, 160))
        
        col_width = 240
        y_start = 200
        line_height = 28
        max_rows = 10  # Максимум строк в колонке
        
        # Считаем начальную позицию по X для центровки двух колонок
        total_width = col_width * 2
        start_x = WIDTH // 2 - total_width // 2
        
        for i, text in enumerate(upgrade_texts):
            col = i // max_rows
            row = i % max_rows
            x = start_x + col * col_width
            y = y_start + row * line_height
            rendered = self.font_tiny.render(text, True, COLORS["ui"])
            screen.blit(rendered, (x, y))
        
        button_width, button_height = 400, 70  # Уменьшено
        start_y = HEIGHT // 2 + 120  # Опущено ниже
        spacing = 90
        
        buttons = [
            {"text": "ПРОДОЛЖИТЬ", "action": "resume"},
            {"text": "ГЛАВНОЕ МЕНЮ", "action": "menu"}
        ]
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = pygame.mouse.get_pressed()[0]
        
        for i, btn_data in enumerate(buttons):
            button_rect = pygame.Rect(
                WIDTH // 2 - button_width // 2,
                start_y + i * spacing,
                button_width,
                button_height
            )
            
            is_hover = button_rect.collidepoint(mouse_pos)
            
            button_color = COLORS["card"] if not is_hover else (40, 45, 65)
            pygame.draw.rect(screen, button_color, button_rect, border_radius=12)
            
            border_color = COLORS["player"] if is_hover else COLORS["card_border"]
            border_width = 4 if is_hover else 2
            pygame.draw.rect(screen, border_color, button_rect, border_width, border_radius=12)
            
            text_color = COLORS["player"] if is_hover else COLORS["ui"]
            button_text = self.font_medium.render(btn_data["text"], True, text_color)
            text_rect = button_text.get_rect(center=button_rect.center)
            screen.blit(button_text, text_rect)
            
            if is_hover and mouse_clicked and not self.pause_click_handled:
                self.pause_click_handled = True
                if btn_data["action"] == "resume":
                    self.state = GameState.PLAY
                elif btn_data["action"] == "menu":
                    self.state = GameState.MENU
                    self.menu_page = "main"
                pygame.time.delay(200)
        
        hint = self.font_small.render("ESC - продолжить", True, (150, 150, 170))
        hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT - 80))
        screen.blit(hint, hint_rect)
    
    def draw_game_over(self):
        # Dark gradient background
        for _i in range(HEIGHT):
            _p = _i / HEIGHT
            pygame.draw.line(screen, (int(18-10*_p), int(5-2*_p), int(5-2*_p)), (0,_i),(WIDTH,_i))
        
        cx = WIDTH // 2
        mouse_pos = pygame.mouse.get_pos()
        
        # Title - fixed position relative to top
        title = self.font_huge.render("GAME OVER", True, COLORS["enemy"])
        screen.blit(title, title.get_rect(center=(cx, int(HEIGHT * 0.18))))
        
        # Stats card - centered
        card_w, card_h = 640, 240
        card_x = cx - card_w // 2
        card_y = int(HEIGHT * 0.30)
        pygame.draw.rect(screen, (22, 10, 10), (card_x, card_y, card_w, card_h), border_radius=14)
        pygame.draw.rect(screen, (120, 30, 30), (card_x, card_y, card_w, card_h), 2, border_radius=14)
        
        # Stats in 2 rows
        stats_top = [
            ("СЧЁТ",    str(self.score),               COLORS["warning"]),
            ("УРОВЕНЬ", str(self.player.level),         COLORS["player"]),
            ("ВОЛНА",   str(self.wave_system.current_wave), COLORS["exp"]),
        ]
        stats_bot = [
            ("УБИЙСТВ", str(self.kills),               COLORS["enemy"]),
            ("ВЫЖИТО",  f"{int(self.time_survived)}с",  COLORS["ui"]),
        ]
        
        col_w = card_w // 3
        for i, (lbl, val, col) in enumerate(stats_top):
            sx = card_x + i * col_w + col_w // 2
            lt = self.font_tiny.render(lbl, True, (160, 150, 150))
            screen.blit(lt, lt.get_rect(center=(sx, card_y + 50)))
            vt = self.font_medium.render(val, True, col)
            screen.blit(vt, vt.get_rect(center=(sx, card_y + 85)))
        
        col_w2 = card_w // 2
        for i, (lbl, val, col) in enumerate(stats_bot):
            sx = card_x + i * col_w2 + col_w2 // 2
            lt = self.font_tiny.render(lbl, True, (160, 150, 150))
            screen.blit(lt, lt.get_rect(center=(sx, card_y + 140)))
            vt = self.font_medium.render(val, True, col)
            screen.blit(vt, vt.get_rect(center=(sx, card_y + 175)))
        
        # Currency earned
        earned = self.kills + self.player.level * 10 + self.wave_system.current_wave * 20
        earned_t = self.font_small.render(f"Заработано: +{earned} валюты", True, COLORS["warning"])
        screen.blit(earned_t, earned_t.get_rect(center=(cx, card_y + card_h + 30)))
        
        # Buttons
        btn_y = card_y + card_h + 65
        for i, (label, action) in enumerate([("ИГРАТЬ СНОВА", "restart"), ("ГЛАВНОЕ МЕНЮ", "menu")]):
            bx = cx - 215 + i * 230
            brect = pygame.Rect(bx, btn_y, 200, 55)
            is_hover = brect.collidepoint(mouse_pos)
            if i == 0:
                bg = COLORS["player"] if is_hover else (0, 80, 70)
                border = COLORS["player"]
            else:
                bg = (50, 55, 75) if is_hover else (28, 32, 48)
                border = COLORS["card_border"]
            pygame.draw.rect(screen, bg, brect, border_radius=10)
            pygame.draw.rect(screen, border, brect, 2, border_radius=10)
            tc = COLORS["bg"] if (i == 0 and is_hover) else (COLORS["ui"])
            bt = self.font_small.render(label, True, tc)
            screen.blit(bt, bt.get_rect(center=brect.center))
            
            if is_hover and pygame.mouse.get_pressed()[0]:
                if action == "restart":
                    self.reset_game()
                    self.state = GameState.PLAY
                else:
                    self.state = GameState.MENU
                    self.menu_page = "main"
                pygame.time.delay(200)
    
    def _activate_ability(self, ab_id):
        """Активировать выбранную способность"""
        AB_COOLDOWNS = {"dash_boost":0,"shield_pulse":6000,"time_slow":12000,"overdrive":15000,"nuke":20000,
                        "heal_pulse":18000,"bullet_storm":10000}
        self.ability_cooldown = AB_COOLDOWNS.get(ab_id, 8000)
        
        if ab_id == "dash_boost":
            # Рывок наносит урон — флаг уже устанавливается при рывке
            self.player.dash_deals_damage = True
        
        elif ab_id == "shield_pulse":
            # Push enemies away
            self.ability_active_timer = 300
            push_radius = 250
            push_force = 18
            for enemy in self.enemies:
                d = enemy.pos - self.player.pos
                if d.length() < push_radius:
                    if d.length() > 0:
                        enemy.pos += d.normalize() * push_force
            # Visual particle burst
            self.particle_system.emit(self.player.pos, 30, COLORS["shield"])
            self.sound_manager.play_sound("explosion")
        
        elif ab_id == "time_slow":
            # Замедляет всех врагов (не замораживает)
            self.ability_active_timer = 4000
            for enemy in self.enemies:
                enemy.slow_duration = max(enemy.slow_duration, 4000)
                enemy.slow_factor = min(enemy.slow_factor, 0.4)
            self.particle_system.emit(self.player.pos, 20, (100, 200, 255))
        
        elif ab_id == "overdrive":
            # Double fire rate temporarily
            self.ability_active_timer = 5000
            self._orig_fire_rate = self.player.fire_rate
            self.player.fire_rate = max(50, self.player.fire_rate // 2)
            self._overdrive_active = True
            self.particle_system.emit(self.player.pos, 25, COLORS["warning"])
        
        elif ab_id == "nuke":
            # Huge AOE damage
            nuke_radius = 400
            nuke_dmg = 150
            for enemy in self.enemies[:]:
                d = (enemy.pos - self.player.pos).length()
                if d < nuke_radius:
                    if enemy.take_damage(nuke_dmg):
                        self.particle_system.emit(enemy.pos, 20, enemy.color)
                        self.exp_gems.append(pygame.Vector2(enemy.pos))
                        self.enemies.remove(enemy)
                        self.kills += 1
                        self.score += enemy.exp_value
            self.particle_system.emit(self.player.pos, 60, (255, 100, 0))
            self.sound_manager.play_sound("explosion")
        
        elif ab_id == "heal_pulse":
            # Восстанавливает 40% HP и временный щит
            heal_amount = int(self.player.max_hp * 0.4)
            self.player.heal(heal_amount)
            # Временный щит на 3 секунды (добавляем 50 щита)
            if not hasattr(self.player, '_pulse_shield_active'):
                self.player._pulse_shield_active = False
            self.player.add_shield(80)
            self.ability_active_timer = 3000
            self.particle_system.emit(self.player.pos, 25, (100, 255, 150))
            self.sound_manager.play_sound("powerup")
        
        elif ab_id == "bullet_storm":
            # 24 пули во все стороны
            import math as _m
            for bi in range(24):
                angle = bi * (360 / 24)
                is_crit = random.random() < self.player.crit_chance
                dmg = int(self.player.dmg * (self.player.crit_multiplier if is_crit else 1))
                self.bullets.append(Bullet(
                    self.player.pos, angle, self.player.bullet_speed * 1.2,
                    dmg, self.player.piercing, self.player.bullet_size,
                    self.player.bullet_lifetime, is_crit
                ))
            self.particle_system.emit(self.player.pos, 30, COLORS["player"])
            self.sound_manager.play_sound("shoot")

    def game_loop(self):
        self.time_survived += self.dt
        
        # Update ability cooldown
        if self.ability_cooldown > 0:
            self.ability_cooldown -= self.dt * 1000
            if self.ability_cooldown < 0:
                self.ability_cooldown = 0
        if self.ability_active_timer > 0:
            self.ability_active_timer -= self.dt * 1000
            if self.ability_active_timer <= 0:
                self.ability_active_timer = 0
                # Revert overdrive when it expires
                if hasattr(self, '_overdrive_active') and self._overdrive_active:
                    self._overdrive_active = False
                    self.player.fire_rate = getattr(self, '_orig_fire_rate', self.player.fire_rate)
        
        self.player.update(self.dt)
        self.update_player_input()
        self.update_shooting()
        
        target_cam = pygame.Vector2(WIDTH // 2, HEIGHT // 2) - self.player.pos
        self.cam += (target_cam - self.cam) * 0.1
        
        self.spawn_enemies()
        self.update_wave_system()
        
        for enemy in self.enemies[:]:
            enemy.update(self.dt, self.player.pos, self.enemies)
            # Удаляем врагов убитых эффектами (яд и т.д.)
            if enemy.hp <= 0 and enemy in self.enemies:
                self.particle_system.emit(enemy.pos, 15, enemy.color)
                self.exp_gems.append(pygame.Vector2(enemy.pos))
                self.enemies.remove(enemy)
                self.kills += 1
                self.score += enemy.exp_value
                if self.player.lifesteal > 0:
                    self.player.heal(int(5 * self.player.lifesteal))
        
        for bullet in self.bullets[:]:
            if bullet.update(self.dt):
                self.bullets.remove(bullet)
        
        self.update_combat()
        self.update_exp_gems()
        self.particle_system.update(self.dt)
        
        # Проверяем достижения каждые 3 секунды
        if not hasattr(self, '_ach_timer'):
            self._ach_timer = 0
        self._ach_timer += self.dt
        if self._ach_timer >= 3.0:
            self._ach_timer = 0
            AchievementSystem.check_achievements(self, self.save_system)
        
        # РИСОВАНИЕ
        self.draw_background()
        self.particle_system.draw(screen, self.cam)
        
        for gem in self.exp_gems:
            glow_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*COLORS["exp_glow"], 80), (15, 15), 12)
            screen.blit(glow_surf, (gem.x + self.cam.x - 15, gem.y + self.cam.y - 15))
            pygame.draw.circle(screen, COLORS["exp"], 
                             (int(gem.x + self.cam.x), int(gem.y + self.cam.y)), 5)
        
        for enemy in self.enemies:
            enemy.draw(screen, self.cam)
        
        for bullet in self.bullets:
            bullet.draw(screen, self.cam)
        
        # Снаряды врагов
        if hasattr(self, 'enemy_bullets'):
            for eb in self.enemy_bullets:
                ex = int(eb['pos'].x + self.cam.x)
                ey = int(eb['pos'].y + self.cam.y)
                if eb['type'] == 'mortar':
                    # Мортира мигает
                    pulse = int(180 + 75 * abs(math.sin(pygame.time.get_ticks() / 150)))
                    pygame.draw.circle(screen, (pulse, 120, 20), (ex, ey), eb['size'])
                    pygame.draw.circle(screen, (255, 200, 0), (ex, ey), eb['size'], 2)
                else:
                    pygame.draw.circle(screen, eb['color'], (ex, ey), eb['size'])
        
        self.player.draw(screen, self.cam)
        self.draw_ui()
    
    def run(self):
        while True:
            self.dt = self.clock.tick(FPS) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if self.rebinding_key is not None:
                        self.save_system.data["controls"][self.rebinding_key] = event.key
                        self.save_system.save()
                        self.rebinding_key = None
                    
                    if event.key == pygame.K_ESCAPE:
                        if self.state == GameState.PLAY:
                            self.state = GameState.PAUSE
                            self.pause_click_handled = False
                        elif self.state == GameState.PAUSE:
                            self.state = GameState.PLAY
                        elif self.state == GameState.WAVE_COMPLETE:
                            self.state = GameState.PAUSE
                            self.pause_click_handled = False
                        elif self.state == GameState.MENU:
                            if self.menu_page != "main":
                                self.menu_page = "main"
                    
                    # Active ability key - configurable (default Q)
                    ability_key = self.save_system.data["controls"].get("ability", pygame.K_q)
                    if self.state == GameState.PLAY and self.ability_cooldown <= 0:
                        active_ab = self.save_system.data.get("active_ability", "")
                        if active_ab and event.key == ability_key:
                            owned = self.save_system.data.get("owned_abilities", [])
                            if active_ab in owned:
                                self._activate_ability(active_ab)
                    
                    # Переключение автострельбы настраиваемой кнопкой
                    auto_fire_key = self.save_system.data["controls"].get("auto_fire_toggle", pygame.K_TAB)
                    if event.key == auto_fire_key and self.state in [GameState.PLAY, GameState.WAVE_COMPLETE]:
                        self.save_system.data["settings"]["auto_fire"] = not self.save_system.data["settings"]["auto_fire"]
                        self.save_system.save()
                
                # Прокрутка колесиком мыши для меню достижений
                if event.type == pygame.MOUSEWHEEL:
                    if self.state == GameState.MENU and self.menu_page == "achievements":
                        # Вычисляем максимальную прокрутку
                        achievements_count = len(AchievementSystem.ACHIEVEMENTS)
                        card_height = 90
                        spacing = 15
                        container_h = HEIGHT - 330
                        total_content_height = achievements_count * (card_height + spacing)
                        max_scroll = max(0, total_content_height - container_h + 40)
                        
                        scroll_speed = 30
                        self.achievements_scroll_offset -= event.y * scroll_speed
                        self.achievements_scroll_offset = max(0, min(max_scroll, self.achievements_scroll_offset))
                    
                    elif self.state == GameState.MENU and self.menu_page == "skins":
                        if not hasattr(self, 'skins_scroll'):
                            self.skins_scroll = 0
                        # Calculate max_scroll from content
                        _skins_total_h = sum(
                            (100 + 12) if sk in self.save_system.data.get("unlocked_skins", ["default"]) else (70 + 12)
                            for sk in PLAYER_SKINS
                        )
                        _skins_max = max(0, _skins_total_h - (HEIGHT - 280) + 40)
                        self.skins_scroll = max(0, min(_skins_max, self.skins_scroll - event.y * 30))
                    
                    elif self.state == GameState.MENU and self.menu_page == "knowledge":
                        if not hasattr(self, 'knowledge_scroll'):
                            self.knowledge_scroll = 0
                        self.knowledge_scroll = max(0, self.knowledge_scroll - event.y * 30)
                    
                    elif self.state == GameState.MENU and self.menu_page == "settings":
                        if not hasattr(self, 'settings_scroll'):
                            self.settings_scroll = 0
                        self.settings_scroll = max(0, self.settings_scroll - event.y * 30)
                
                if event.type == pygame.MOUSEBUTTONUP:
                    self.pause_click_handled = False
                    self.level_up_click_handled = False
                    self._skin_click_handled = False
                    self._reward_claim_handled = False
                    self._mod_click = False
                    self._ab_click = False
                    # Reset per-achievement claim flags
                    for key in list(vars(self).keys()):
                        if key.startswith('_ach_click_'):
                            setattr(self, key, False)
            
            if self.state == GameState.MENU:
                self.menu_time += self.dt
                self.draw_menu()
            
            elif self.state == GameState.MODE_SELECT:
                self.draw_mode_select()
            
            elif self.state == GameState.PLAY:
                self.game_loop()
            
            elif self.state == GameState.LEVEL_UP:
                self.draw_background()
                for enemy in self.enemies:
                    enemy.draw(screen, self.cam)
                self.player.draw(screen, self.cam)
                self.draw_level_up()
            
            elif self.state == GameState.WAVE_COMPLETE:
                # Игра продолжается, только не спавнятся враги
                self.time_survived += self.dt
                
                self.player.update(self.dt)
                self.update_player_input()
                self.update_shooting()
                
                target_cam = pygame.Vector2(WIDTH // 2, HEIGHT // 2) - self.player.pos
                self.cam += (target_cam - self.cam) * 0.1
                
                for enemy in self.enemies[:]:
                    enemy.update(self.dt, self.player.pos, self.enemies)
                    if enemy.hp <= 0 and enemy in self.enemies:
                        self.particle_system.emit(enemy.pos, 10, enemy.color)
                        self.exp_gems.append(pygame.Vector2(enemy.pos))
                        self.enemies.remove(enemy)
                        self.kills += 1
                        self.score += enemy.exp_value
                
                for bullet in self.bullets[:]:
                    if bullet.update(self.dt):
                        self.bullets.remove(bullet)
                
                self.update_combat()
                self.update_exp_gems()
                self.particle_system.update(self.dt)
                
                # Рисование
                self.draw_background()
                self.particle_system.draw(screen, self.cam)
                
                for gem in self.exp_gems:
                    glow_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (*COLORS["exp_glow"], 80), (15, 15), 12)
                    screen.blit(glow_surf, (gem.x + self.cam.x - 15, gem.y + self.cam.y - 15))
                    pygame.draw.circle(screen, COLORS["exp"], 
                                     (int(gem.x + self.cam.x), int(gem.y + self.cam.y)), 5)
                
                for enemy in self.enemies:
                    enemy.draw(screen, self.cam)
                
                for bullet in self.bullets:
                    bullet.draw(screen, self.cam)
                
                # Снаряды врагов
                if hasattr(self, 'enemy_bullets'):
                    for eb in self.enemy_bullets:
                        ex = int(eb['pos'].x + self.cam.x)
                        ey = int(eb['pos'].y + self.cam.y)
                        pygame.draw.circle(screen, eb['color'], (ex, ey), eb['size'])
                
                self.player.draw(screen, self.cam)
                self.draw_ui()
                self.draw_wave_complete()
                
                # Автоматически обновляем перерыв
                if self.wave_system.update_break(self.dt):
                    self.wave_system.start_wave()
                    self.state = GameState.PLAY
            
            elif self.state == GameState.PAUSE:
                self.draw_background()
                for gem in self.exp_gems:
                    pygame.draw.circle(screen, COLORS["exp"], 
                                     (int(gem.x + self.cam.x), int(gem.y + self.cam.y)), 5)
                for enemy in self.enemies:
                    enemy.draw(screen, self.cam)
                for bullet in self.bullets:
                    bullet.draw(screen, self.cam)
                self.player.draw(screen, self.cam)
                self.draw_ui()
                self.draw_pause()
            
            elif self.state == GameState.GAME_OVER:
                self.draw_game_over()
            
            # Рисуем курсор поверх всего
            self.draw_cursor()
            
            pygame.display.flip()