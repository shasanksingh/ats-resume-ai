"use client";

import { useEffect, useRef } from "react";

type Point = { x: number; y: number };

const TRAIL_POINTS = 42;
const MAX_POINT_SPACING = 9;

export function CursorLine() {
  const svg = useRef<SVGSVGElement | null>(null);
  const path = useRef<SVGPathElement | null>(null);
  const head = useRef<SVGCircleElement | null>(null);
  const gradient = useRef<SVGLinearGradientElement | null>(null);

  useEffect(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (reducedMotion.matches) return;

    const start = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
    const points: Point[] = [];
    const target = { ...start };
    const cursor = { ...start };
    let initialized = false;
    let visible = false;
    let lastMoveAt = 0;
    let frame = window.requestAnimationFrame(animate);

    const resize = () => {
      if (!svg.current) return;
      svg.current.setAttribute("viewBox", `0 0 ${window.innerWidth} ${window.innerHeight}`);
    };
    const move = (event: PointerEvent) => {
      target.x = event.clientX;
      target.y = event.clientY;
      lastMoveAt = performance.now();

      if (!initialized) {
        cursor.x = target.x;
        cursor.y = target.y;
        seedPoints(points, target);
        initialized = true;
      }

      visible = true;
    };
    const leave = () => {
      visible = false;
    };

    resize();

    function animate(now: number) {
      if (!initialized) {
        frame = window.requestAnimationFrame(animate);
        return;
      }

      cursor.x += (target.x - cursor.x) * 0.42;
      cursor.y += (target.y - cursor.y) * 0.42;
      addInterpolatedPoint(points, cursor);
      points.length = Math.min(points.length, TRAIL_POINTS);

      const d = buildSmoothPath(points);
      const tail = points[points.length - 1];
      const opacity = visible ? Math.max(0, 1 - Math.max(0, now - lastMoveAt - 550) / 900) : 0;

      if (gradient.current && tail) {
        gradient.current.setAttribute("x1", tail.x.toFixed(1));
        gradient.current.setAttribute("y1", tail.y.toFixed(1));
        gradient.current.setAttribute("x2", cursor.x.toFixed(1));
        gradient.current.setAttribute("y2", cursor.y.toFixed(1));
      }

      if (path.current) {
        path.current.setAttribute("d", d);
        path.current.style.opacity = String(opacity);
      }
      if (head.current) {
        head.current.setAttribute("cx", cursor.x.toFixed(1));
        head.current.setAttribute("cy", cursor.y.toFixed(1));
        head.current.style.opacity = String(opacity);
      }

      frame = window.requestAnimationFrame(animate);
    }

    window.addEventListener("pointermove", move, { passive: true });
    window.addEventListener("resize", resize);
    document.documentElement.addEventListener("mouseleave", leave);
    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener("pointermove", move);
      window.removeEventListener("resize", resize);
      document.documentElement.removeEventListener("mouseleave", leave);
    };
  }, []);

  return (
    <svg ref={svg} className="cursor-comet-effect" aria-hidden="true">
      <defs>
        <linearGradient ref={gradient} id="cursor-comet-gradient" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="rgb(99 102 241)" stopOpacity="0" />
          <stop offset="62%" stopColor="rgb(99 102 241)" stopOpacity="0.28" />
          <stop offset="100%" stopColor="rgb(34 211 238)" stopOpacity="0.95" />
        </linearGradient>
      </defs>
      <path ref={path} className="cursor-comet-path" />
      <circle ref={head} className="cursor-comet-head" r="4.5" />
    </svg>
  );
}

function buildSmoothPath(points: Point[]) {
  const tail = points.slice().reverse();
  if (tail.length < 2) return "";

  let d = `M ${tail[0].x.toFixed(1)} ${tail[0].y.toFixed(1)}`;
  for (let index = 0; index < tail.length - 1; index += 1) {
    const p0 = tail[Math.max(0, index - 1)];
    const p1 = tail[index];
    const p2 = tail[index + 1];
    const p3 = tail[Math.min(tail.length - 1, index + 2)];
    const cp1 = {
      x: p1.x + (p2.x - p0.x) / 6,
      y: p1.y + (p2.y - p0.y) / 6
    };
    const cp2 = {
      x: p2.x - (p3.x - p1.x) / 6,
      y: p2.y - (p3.y - p1.y) / 6
    };
    d += ` C ${cp1.x.toFixed(1)} ${cp1.y.toFixed(1)} ${cp2.x.toFixed(1)} ${cp2.y.toFixed(1)} ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
  }

  return d;
}

function seedPoints(points: Point[], point: Point) {
  points.length = 0;
  for (let index = 0; index < TRAIL_POINTS; index += 1) {
    points.push({ ...point });
  }
}

function addInterpolatedPoint(points: Point[], point: Point) {
  const previous = points[0];
  if (!previous) {
    points.unshift({ ...point });
    return;
  }

  const distance = Math.hypot(point.x - previous.x, point.y - previous.y);
  const steps = Math.max(1, Math.ceil(distance / MAX_POINT_SPACING));

  for (let step = 1; step <= steps; step += 1) {
    const progress = step / steps;
    points.unshift({
      x: previous.x + (point.x - previous.x) * progress,
      y: previous.y + (point.y - previous.y) * progress
    });
  }
}
