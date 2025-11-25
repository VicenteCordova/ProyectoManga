(function () {
  "use strict";

  const canvas = document.getElementById("stars-canvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d", { alpha: true });
  let w, h, dpr, stars;

  function resize() {
    dpr = window.devicePixelRatio || 1;
    w = canvas.clientWidth = window.innerWidth;
    h = canvas.clientHeight = window.innerHeight;
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    initStars();
  }

  function initStars() {
    const count = Math.floor((w * h) / 12000); // densidad ajustada
    stars = new Array(count).fill(0).map(() => ({
      x: Math.random() * w,
      y: Math.random() * h,
      r: Math.random() * 1.1 + 0.3,          // radio
      vx: (Math.random() - 0.5) * 0.06,      // velocidad X
      vy: (Math.random() - 0.5) * 0.06,      // velocidad Y
      a: Math.random() * Math.PI * 2,        // fase para twinkle
      tw: 0.25 + Math.random() * 0.75        // intensidad de twinkle
    }));
  }

  function step() {
    ctx.clearRect(0, 0, w, h);
    for (const s of stars) {
      s.x += s.vx;
      s.y += s.vy;
      s.a += 0.02;

      // wrap-around
      if (s.x < -5) s.x = w + 5;
      if (s.x > w + 5) s.x = -5;
      if (s.y < -5) s.y = h + 5;
      if (s.y > h + 5) s.y = -5;

      const twinkle = 0.5 + Math.sin(s.a) * 0.5; // 0..1
      const alpha = 0.3 + twinkle * s.tw * 0.7;  // 0.3..1

      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,255,255,${alpha.toFixed(3)})`;
      ctx.fill();
    }
    requestAnimationFrame(step);
  }

  window.addEventListener("resize", resize, { passive: true });
  resize();
  requestAnimationFrame(step);
})();
