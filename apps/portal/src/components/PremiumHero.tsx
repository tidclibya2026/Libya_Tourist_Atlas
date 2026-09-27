"use client";
import Image from "next/image";
import { useEffect, useState } from "react";
import { heroSlides } from "../data/atlasMedia";
import styles from "./PremiumHero.module.css";

export default function PremiumHero() {
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);
  const slide = heroSlides[active];

  useEffect(() => {
    if (paused) return;
    const timer = window.setInterval(() => {
      setActive((current) => (current + 1) % heroSlides.length);
    }, 6500);
    return () => window.clearInterval(timer);
  }, [paused]);

  return (
    <section className={styles.hero} aria-label="عرض الوجهات السياحية">
      <div className={styles.stage}>
        {heroSlides.map((item, index) => (
          <div
            key={item.id}
            aria-hidden={index !== active}
            className={`${styles.slide} ${active === index ? styles.current : ""}`}
          >
            <Image
              src={item.image}
              alt={active === index ? item.title : ""}
              fill
              sizes="100vw"
              priority={index === 0}
              unoptimized
              className={styles.photo}
            />
          </div>
        ))}
        <div className={styles.photoBadge}>LIBYA TOURISM ATLAS · V2.3</div>
        <div className={styles.controls}>
          <button type="button" onClick={() => setActive((active + heroSlides.length - 1) % heroSlides.length)} aria-label="الصورة السابقة">‹</button>
          <span aria-live="polite">{String(active + 1).padStart(2, "0")} / {String(heroSlides.length).padStart(2, "0")}</span>
          <button type="button" onClick={() => setActive((active + 1) % heroSlides.length)} aria-label="الصورة التالية">›</button>
        </div>
      </div>
      <div className={styles.caption}>
        <div className={styles.story}>
          <span className={styles.eyebrow}>الأطلس السياحي الرقمي الوطني الليبي</span>
          <h1>ليبيا... وجهات تتجاوز التوقعات</h1>
          <p>استكشف الآثار والتراث والثقافة والطبيعة والاستثمار عبر بوابة سياحية وطنية متكاملة.</p>
          <div className={styles.actions}>
            <a href="#destinations">استكشف الوجهات</a>
            <a className={styles.secondary} href="#sectors">قطاعات الأطلس</a>
          </div>
        </div>
        <div className={styles.currentText} aria-live="polite">
          <span>{slide.category}</span>
          <h2>{slide.title}</h2>
          <p>{slide.description}</p>
          <button type="button" onClick={() => setPaused((value) => !value)} aria-pressed={paused}>{paused ? "استئناف العرض ◀" : "إيقاف مؤقت Ⅱ"}</button>
        </div>
      </div>
      <div className={styles.dots} aria-label="اختيار صورة الوجهة">
        {heroSlides.map((item, index) => (
          <button
            type="button"
            key={item.id}
            onClick={() => setActive(index)}
            aria-label={`عرض صورة ${item.title}`}
            aria-pressed={index === active}
            className={index === active ? styles.dotActive : styles.dot}
          />
        ))}
      </div>
    </section>
  );
}
