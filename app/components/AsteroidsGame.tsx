'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

// ---- Types ----
interface Vec2 { x: number; y: number; }
interface Star { x: number; y: number; size: number; twinkle: number; }
interface Asteroid { pos: Vec2; vel: Vec2; angle: number; angVel: number; radius: number; tier: number; verts: Vec2[]; }
interface Bullet { pos: Vec2; vel: Vec2; life: number; }
interface Particle { pos: Vec2; vel: Vec2; life: number; maxLife: number; size: number; hue: number; }
interface Ship { pos: Vec2; vel: Vec2; angle: number; invincible: number; shootCooldown: number; }
type Phase = 'start' | 'playing' | 'dead' | 'gameover';

interface Game {
  ship: Ship | null;
  asteroids: Asteroid[];
  bullets: Bullet[];
  particles: Particle[];
  stars: Star[];
  score: number;
  lives: number;
  level: number;
  phase: Phase;
  respawnTimer: number;
  levelSpeedMult: number;
}

// ---- Constants ----
const SHIP_R = 16;
const ROTATE_SPD = 3.8;
const THRUST = 280;
const MAX_SPD = 420;
const FRICTION = 0.995;
const BULLET_SPD = 620;
const BULLET_LIFE = 0.78;
const SHOOT_COOLDOWN = 0.18;
const MAX_BULLETS = 6;

const TIERS: (null | { r: number; spd: number; pts: number; verts: number })[] = [
  null,
  { r: 13, spd: 145, pts: 100, verts: 7 }, // small
  { r: 28, spd: 82,  pts: 50,  verts: 8 }, // medium
  { r: 50, spd: 48,  pts: 20,  verts: 10 }, // large
];

// ---- Math helpers ----
const wrap  = (v: number, max: number) => ((v % max) + max) % max;
const dist  = (a: Vec2, b: Vec2)       => Math.hypot(a.x - b.x, a.y - b.y);
const clampLen = (v: Vec2, max: number): Vec2 => {
  const l = Math.hypot(v.x, v.y);
  return l > max ? { x: v.x * max / l, y: v.y * max / l } : v;
};

// ---- Factory functions ----
function makeVerts(count: number, r: number): Vec2[] {
  return Array.from({ length: count }, (_, i) => {
    const a  = (i / count) * Math.PI * 2;
    const rr = r * (0.68 + Math.random() * 0.58);
    return { x: Math.cos(a) * rr, y: Math.sin(a) * rr };
  });
}

function makeAsteroid(x: number, y: number, tier: number, speedMult = 1): Asteroid {
  const t   = TIERS[tier]!;
  const a   = Math.random() * Math.PI * 2;
  const spd = t.spd * speedMult * (0.7 + Math.random() * 0.6);
  return {
    pos: { x, y },
    vel: { x: Math.cos(a) * spd, y: Math.sin(a) * spd },
    angle: Math.random() * Math.PI * 2,
    angVel: (Math.random() - 0.5) * 1.8,
    radius: t.r,
    tier,
    verts: makeVerts(t.verts, t.r),
  };
}

function makeShip(w: number, h: number): Ship {
  return { pos: { x: w / 2, y: h / 2 }, vel: { x: 0, y: 0 }, angle: -Math.PI / 2, invincible: 3, shootCooldown: 0 };
}

function makeStars(w: number, h: number): Star[] {
  return Array.from({ length: 160 }, () => ({
    x: Math.random() * w,
    y: Math.random() * h,
    size: Math.random() * 1.8 + 0.2,
    twinkle: Math.random() * Math.PI * 2,
  }));
}

function makeWave(w: number, h: number, level: number, speedMult: number): Asteroid[] {
  const count  = 3 + Math.floor(level * 0.9);
  const center = { x: w / 2, y: h / 2 };
  return Array.from({ length: count }, () => {
    let x: number, y: number;
    do { x = Math.random() * w; y = Math.random() * h; } while (dist({ x, y }, center) < 160);
    return makeAsteroid(x, y, 3, speedMult);
  });
}

function addExplosion(particles: Particle[], pos: Vec2, count: number, hue: number) {
  for (let i = 0; i < count; i++) {
    const a    = Math.random() * Math.PI * 2;
    const spd  = 30 + Math.random() * 150;
    const life = 0.25 + Math.random() * 0.65;
    particles.push({
      pos: { ...pos },
      vel: { x: Math.cos(a) * spd, y: Math.sin(a) * spd },
      life, maxLife: life,
      size: 1.5 + Math.random() * 2.5,
      hue,
    });
  }
}

// ---- Draw functions ----
function drawStar(ctx: CanvasRenderingContext2D, s: Star, t: number) {
  const alpha = 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(t * 0.7 + s.twinkle));
  ctx.globalAlpha = alpha;
  ctx.fillStyle   = '#ffffff';
  ctx.fillRect(s.x, s.y, s.size, s.size);
}

function drawAsteroid(ctx: CanvasRenderingContext2D, a: Asteroid) {
  ctx.save();
  ctx.translate(a.pos.x, a.pos.y);
  ctx.rotate(a.angle);
  ctx.shadowBlur   = 12;
  ctx.shadowColor  = '#5577aa';
  ctx.strokeStyle  = '#99aabb';
  ctx.lineWidth    = 1.5;
  ctx.beginPath();
  ctx.moveTo(a.verts[0].x, a.verts[0].y);
  for (let i = 1; i < a.verts.length; i++) ctx.lineTo(a.verts[i].x, a.verts[i].y);
  ctx.closePath();
  ctx.stroke();
  ctx.restore();
}

function drawBullet(ctx: CanvasRenderingContext2D, b: Bullet) {
  ctx.save();
  ctx.shadowBlur  = 16;
  ctx.shadowColor = '#00ffee';
  ctx.fillStyle   = '#aaffee';
  ctx.beginPath();
  ctx.arc(b.pos.x, b.pos.y, 2.8, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawShip(ctx: CanvasRenderingContext2D, ship: Ship, thrusting: boolean) {
  if (ship.invincible > 0 && Math.floor(ship.invincible * 8) % 2 === 0) return;
  ctx.save();
  ctx.translate(ship.pos.x, ship.pos.y);
  ctx.rotate(ship.angle);

  // Thruster flame
  if (thrusting) {
    const fl = 14 + Math.random() * 12;
    ctx.save();
    ctx.shadowBlur  = 24;
    ctx.shadowColor = '#00aaff';
    ctx.strokeStyle = '#55ccff';
    ctx.lineWidth   = 3.5;
    ctx.beginPath();
    ctx.moveTo(-SHIP_R * 0.58, -5);
    ctx.lineTo(-SHIP_R * 0.58 - fl, 0);
    ctx.lineTo(-SHIP_R * 0.58, 5);
    ctx.stroke();
    ctx.restore();
  }

  // Glow
  ctx.shadowBlur   = 18;
  ctx.shadowColor  = '#00ffff';
  ctx.strokeStyle  = '#ffffff';
  ctx.lineWidth    = 2;
  ctx.beginPath();
  ctx.moveTo(SHIP_R, 0);
  ctx.lineTo(-SHIP_R * 0.65, -SHIP_R * 0.55);
  ctx.lineTo(-SHIP_R * 0.38, 0);
  ctx.lineTo(-SHIP_R * 0.65, SHIP_R * 0.55);
  ctx.closePath();
  ctx.stroke();

  ctx.restore();
}

function drawParticle(ctx: CanvasRenderingContext2D, p: Particle) {
  const t = p.life / p.maxLife;
  ctx.save();
  ctx.globalAlpha = t * t;
  ctx.shadowBlur  = 10;
  ctx.shadowColor = `hsl(${p.hue},100%,60%)`;
  ctx.fillStyle   = `hsl(${p.hue + 30 * t},100%,72%)`;
  ctx.beginPath();
  ctx.arc(p.pos.x, p.pos.y, Math.max(0.5, p.size * t), 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

// ---- Component ----
export default function AsteroidsGame() {
  const canvasRef  = useRef<HTMLCanvasElement>(null);
  const gameRef    = useRef<Game>({
    ship: null, asteroids: [], bullets: [], particles: [], stars: [],
    score: 0, lives: 3, level: 1,
    phase: 'start', respawnTimer: 0, levelSpeedMult: 1,
  });
  const keysRef    = useRef(new Set<string>());
  const touchRef   = useRef({ left: false, right: false, thrust: false, shoot: false });
  const rafRef     = useRef(0);
  const lastTRef   = useRef(0);

  const [ui, setUi] = useState({ score: 0, lives: 3, level: 1, phase: 'start' as Phase });

  const startGame = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const { width: w, height: h } = canvas;
    const g = gameRef.current;
    g.ship           = makeShip(w, h);
    g.asteroids      = makeWave(w, h, 1, 1);
    g.bullets        = [];
    g.particles      = [];
    g.score          = 0;
    g.lives          = 3;
    g.level          = 1;
    g.phase          = 'playing';
    g.respawnTimer   = 0;
    g.levelSpeedMult = 1;
    setUi({ score: 0, lives: 3, level: 1, phase: 'playing' });
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;

    const resize = () => {
      canvas.width  = canvas.clientWidth;
      canvas.height = canvas.clientHeight;
      gameRef.current.stars = makeStars(canvas.width, canvas.height);
    };
    resize();
    window.addEventListener('resize', resize);

    const onKey = (e: KeyboardEvent) => {
      const down = e.type === 'keydown';
      if (down) keysRef.current.add(e.code);
      else keysRef.current.delete(e.code);
      if (['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.code)) e.preventDefault();
      if (down && (e.code === 'Enter' || e.code === 'Space')) {
        const { phase } = gameRef.current;
        if (phase === 'start' || phase === 'gameover') startGame();
      }
    };
    window.addEventListener('keydown', onKey);
    window.addEventListener('keyup', onKey);

    const loop = (t: number) => {
      const dt    = Math.min((t - lastTRef.current) / 1000, 0.05);
      lastTRef.current = t;
      const g     = gameRef.current;
      const w     = canvas.width;
      const h     = canvas.height;
      const keys  = keysRef.current;
      const touch = touchRef.current;

      // ---- UPDATE ----

      // Demo asteroids in non-playing phases
      if (g.phase === 'start' || g.phase === 'gameover') {
        if (g.asteroids.length < 7) {
          g.asteroids.push(makeAsteroid(Math.random() * w, Math.random() * h, 3, 0.45));
        }
      }

      // Always move asteroids & particles
      g.asteroids.forEach(a => {
        a.pos.x  = wrap(a.pos.x + a.vel.x * dt, w);
        a.pos.y  = wrap(a.pos.y + a.vel.y * dt, h);
        a.angle += a.angVel * dt;
      });
      g.particles.forEach(p => {
        p.pos.x += p.vel.x * dt;
        p.pos.y += p.vel.y * dt;
        p.vel.x *= 0.96;
        p.vel.y *= 0.96;
        p.life  -= dt;
      });
      g.particles = g.particles.filter(p => p.life > 0);

      // Dead phase — wait to respawn
      if (g.phase === 'dead') {
        g.respawnTimer -= dt;
        if (g.respawnTimer <= 0) {
          if (g.lives <= 0) {
            g.phase = 'gameover';
            setUi(u => ({ ...u, phase: 'gameover' }));
          } else {
            g.ship  = makeShip(w, h);
            g.phase = 'playing';
            setUi(u => ({ ...u, phase: 'playing' }));
          }
        }
      }

      // Playing phase — full simulation
      if (g.phase === 'playing' && g.ship) {
        const s     = g.ship;
        const rotL  = keys.has('ArrowLeft')  || keys.has('KeyA') || touch.left;
        const rotR  = keys.has('ArrowRight') || keys.has('KeyD') || touch.right;
        const thrust = keys.has('ArrowUp')   || keys.has('KeyW') || touch.thrust;
        const shoot  = keys.has('Space')     || keys.has('KeyX') || touch.shoot;

        if (rotL) s.angle -= ROTATE_SPD * dt;
        if (rotR) s.angle += ROTATE_SPD * dt;

        if (thrust) {
          s.vel.x += Math.cos(s.angle) * THRUST * dt;
          s.vel.y += Math.sin(s.angle) * THRUST * dt;
          s.vel    = clampLen(s.vel, MAX_SPD);
          // Thruster particles
          if (Math.random() < 0.55) {
            const ba   = s.angle + Math.PI + (Math.random() - 0.5) * 0.5;
            const spd  = 50 + Math.random() * 110;
            const life = 0.1 + Math.random() * 0.2;
            g.particles.push({
              pos: { ...s.pos },
              vel: { x: Math.cos(ba) * spd, y: Math.sin(ba) * spd },
              life, maxLife: life, size: 2 + Math.random() * 2, hue: 188,
            });
          }
        }

        s.vel.x   *= Math.pow(FRICTION, dt * 60);
        s.vel.y   *= Math.pow(FRICTION, dt * 60);
        s.pos.x    = wrap(s.pos.x + s.vel.x * dt, w);
        s.pos.y    = wrap(s.pos.y + s.vel.y * dt, h);
        if (s.invincible > 0) s.invincible -= dt;

        // Shoot
        s.shootCooldown -= dt;
        if (shoot && s.shootCooldown <= 0 && g.bullets.length < MAX_BULLETS) {
          g.bullets.push({
            pos:  { ...s.pos },
            vel:  { x: s.vel.x + Math.cos(s.angle) * BULLET_SPD, y: s.vel.y + Math.sin(s.angle) * BULLET_SPD },
            life: BULLET_LIFE,
          });
          s.shootCooldown = SHOOT_COOLDOWN;
        }

        // Move bullets
        g.bullets.forEach(b => {
          b.pos.x  = wrap(b.pos.x + b.vel.x * dt, w);
          b.pos.y  = wrap(b.pos.y + b.vel.y * dt, h);
          b.life  -= dt;
        });
        g.bullets = g.bullets.filter(b => b.life > 0);

        // Bullet ↔ asteroid collision
        const deadB = new Set<number>();
        const deadA = new Set<number>();
        const newA: Asteroid[] = [];

        g.bullets.forEach((b, bi) => {
          g.asteroids.forEach((a, ai) => {
            if (deadB.has(bi) || deadA.has(ai)) return;
            if (dist(b.pos, a.pos) < a.radius + 2) {
              deadB.add(bi);
              deadA.add(ai);
              g.score += TIERS[a.tier]!.pts;
              setUi(u => ({ ...u, score: g.score }));
              addExplosion(g.particles, a.pos, a.tier * 9, a.tier === 1 ? 200 : 210);
              if (a.tier > 1) {
                newA.push(makeAsteroid(a.pos.x, a.pos.y, a.tier - 1, g.levelSpeedMult));
                newA.push(makeAsteroid(a.pos.x, a.pos.y, a.tier - 1, g.levelSpeedMult));
              }
            }
          });
        });
        g.bullets   = g.bullets.filter((_, i) => !deadB.has(i));
        g.asteroids = g.asteroids.filter((_, i) => !deadA.has(i));
        g.asteroids.push(...newA);

        // Ship ↔ asteroid collision
        if (s.invincible <= 0) {
          for (const a of g.asteroids) {
            if (dist(s.pos, a.pos) < a.radius + SHIP_R - 5) {
              addExplosion(g.particles, s.pos, 40, 28);
              g.lives        -= 1;
              g.phase         = 'dead';
              g.respawnTimer  = g.lives > 0 ? 2.5 : 3;
              g.ship          = null;
              g.bullets       = [];
              setUi(u => ({ ...u, lives: g.lives, phase: 'dead' }));
              break;
            }
          }
        }

        // Level clear
        if (g.asteroids.length === 0) {
          g.level          += 1;
          g.levelSpeedMult  = 1 + (g.level - 1) * 0.1;
          g.asteroids       = makeWave(w, h, g.level, g.levelSpeedMult);
          setUi(u => ({ ...u, level: g.level }));
        }
      }

      // ---- RENDER ----
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = '#050510';
      ctx.fillRect(0, 0, w, h);
      ctx.globalAlpha = 1;

      // Stars
      g.stars.forEach(s => drawStar(ctx, s, t * 0.001));
      ctx.globalAlpha = 1;

      // Game objects
      g.asteroids.forEach(a => drawAsteroid(ctx, a));
      g.bullets.forEach(b => drawBullet(ctx, b));
      g.particles.forEach(p => drawParticle(ctx, p));
      ctx.globalAlpha = 1;

      // Ship
      if (g.ship && g.phase === 'playing') {
        const thrust = keys.has('ArrowUp') || keys.has('KeyW') || touch.thrust;
        drawShip(ctx, g.ship, thrust);
      }

      ctx.globalAlpha = 1;
      ctx.shadowBlur  = 0;

      rafRef.current = requestAnimationFrame(loop);
    };

    rafRef.current = requestAnimationFrame(t => {
      lastTRef.current = t;
      rafRef.current   = requestAnimationFrame(loop);
    });

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener('resize', resize);
      window.removeEventListener('keydown', onKey);
      window.removeEventListener('keyup', onKey);
    };
  }, [startGame]);

  const btnBase = 'select-none touch-none flex items-center justify-center rounded-full border-2 font-bold transition-all active:scale-90';

  return (
    <div className="relative w-full h-full overflow-hidden bg-black" style={{ touchAction: 'none' }}>
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />

      {/* ---- HUD ---- */}
      {(ui.phase === 'playing' || ui.phase === 'dead') && (
        <div className="absolute top-0 left-0 right-0 flex justify-between items-center px-5 py-3 pointer-events-none">
          <span
            className="text-cyan-400 font-mono text-xl font-bold tabular-nums"
            style={{ textShadow: '0 0 12px #00ffff' }}
          >
            {ui.score.toLocaleString()}
          </span>

          <div className="flex gap-2 items-center">
            {Array.from({ length: Math.max(0, ui.lives) }).map((_, i) => (
              <svg key={i} viewBox="-1 -1 2 2" width="16" height="16" className="fill-none stroke-white" strokeWidth="0.18">
                <polygon points="0,-0.88 0.62,0.5 0.22,0.22 0,0.52 -0.22,0.22 -0.62,0.5" />
              </svg>
            ))}
          </div>

          <span
            className="text-purple-400 font-mono text-xl font-bold"
            style={{ textShadow: '0 0 12px #aa44ff' }}
          >
            LVL {ui.level}
          </span>
        </div>
      )}

      {/* ---- Start overlay ---- */}
      {ui.phase === 'start' && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-8 bg-black/50 px-4">
          <div className="text-center">
            <h1
              className="text-6xl sm:text-7xl md:text-8xl lg:text-9xl font-black tracking-[0.15em] text-white"
              style={{ textShadow: '0 0 30px #00ffff, 0 0 60px #0055ff, 0 0 100px #0022ff' }}
            >
              ASTEROIDS
            </h1>
            <p className="text-cyan-500/60 text-sm sm:text-base font-mono tracking-widest mt-3">
              Navigate. Survive. Destroy.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-x-8 gap-y-1 text-xs font-mono text-gray-400 text-center">
            <span className="text-gray-300">← → / A D</span>  <span>Rotate</span>
            <span className="text-gray-300">↑ / W</span>       <span>Thrust</span>
            <span className="text-gray-300">SPACE / X</span>   <span>Fire</span>
          </div>

          <button
            onClick={startGame}
            className="px-12 py-4 border-2 border-cyan-400 text-cyan-300 font-mono text-xl font-bold tracking-[0.25em] hover:bg-cyan-400/15 hover:text-white transition-all rounded-sm cursor-pointer"
            style={{ boxShadow: '0 0 24px rgba(0,255,255,0.35), inset 0 0 24px rgba(0,255,255,0.04)' }}
          >
            LAUNCH
          </button>

          <p className="text-gray-600 font-mono text-xs tracking-widest">PRESS ENTER OR SPACE</p>
        </div>
      )}

      {/* ---- Game Over overlay ---- */}
      {ui.phase === 'gameover' && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-8 bg-black/65 px-4">
          <h2
            className="text-5xl sm:text-6xl md:text-7xl font-black tracking-widest text-red-500"
            style={{ textShadow: '0 0 30px #ff2200, 0 0 60px #ff0000' }}
          >
            GAME OVER
          </h2>

          <div className="text-center space-y-2">
            <p className="text-gray-400 font-mono text-sm tracking-widest uppercase">Final Score</p>
            <p
              className="text-cyan-400 font-mono text-5xl sm:text-6xl font-bold tabular-nums"
              style={{ textShadow: '0 0 20px #00ffff' }}
            >
              {ui.score.toLocaleString()}
            </p>
            <p className="text-gray-500 font-mono text-sm">Level {ui.level} reached</p>
          </div>

          <button
            onClick={startGame}
            className="px-12 py-4 border-2 border-cyan-400 text-cyan-300 font-mono text-xl font-bold tracking-[0.25em] hover:bg-cyan-400/15 hover:text-white transition-all rounded-sm cursor-pointer"
            style={{ boxShadow: '0 0 24px rgba(0,255,255,0.35)' }}
          >
            PLAY AGAIN
          </button>
        </div>
      )}

      {/* ---- Mobile controls ---- */}
      <div className="absolute bottom-6 left-0 right-0 flex justify-between px-5 md:hidden pointer-events-auto">
        {/* Left cluster: rotate */}
        <div className="flex gap-2.5">
          <button
            className={`${btnBase} w-16 h-16 border-white/20 bg-white/10 text-white text-xl`}
            onPointerDown={e => { e.preventDefault(); touchRef.current.left = true; }}
            onPointerUp={() => { touchRef.current.left = false; }}
            onPointerLeave={() => { touchRef.current.left = false; }}
            onPointerCancel={() => { touchRef.current.left = false; }}
          >
            ◄
          </button>
          <button
            className={`${btnBase} w-16 h-16 border-white/20 bg-white/10 text-white text-xl`}
            onPointerDown={e => { e.preventDefault(); touchRef.current.right = true; }}
            onPointerUp={() => { touchRef.current.right = false; }}
            onPointerLeave={() => { touchRef.current.right = false; }}
            onPointerCancel={() => { touchRef.current.right = false; }}
          >
            ►
          </button>
        </div>

        {/* Right cluster: thrust + fire */}
        <div className="flex gap-2.5">
          <button
            className={`${btnBase} w-16 h-16 border-cyan-400/40 bg-cyan-400/10 text-cyan-400 text-xl`}
            onPointerDown={e => {
              e.preventDefault();
              touchRef.current.thrust = true;
              if (gameRef.current.phase === 'start' || gameRef.current.phase === 'gameover') startGame();
            }}
            onPointerUp={() => { touchRef.current.thrust = false; }}
            onPointerLeave={() => { touchRef.current.thrust = false; }}
            onPointerCancel={() => { touchRef.current.thrust = false; }}
          >
            ▲
          </button>
          <button
            className={`${btnBase} w-16 h-16 border-red-400/40 bg-red-400/10 text-red-400 text-xs tracking-wider`}
            onPointerDown={e => {
              e.preventDefault();
              touchRef.current.shoot = true;
              if (gameRef.current.phase === 'start' || gameRef.current.phase === 'gameover') startGame();
            }}
            onPointerUp={() => { touchRef.current.shoot = false; }}
            onPointerLeave={() => { touchRef.current.shoot = false; }}
            onPointerCancel={() => { touchRef.current.shoot = false; }}
          >
            FIRE
          </button>
        </div>
      </div>
    </div>
  );
}
