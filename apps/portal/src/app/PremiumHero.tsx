"use client";

import Image from "next/image";
import { useEffect, useMemo, useState } from "react";
import styles from "./PremiumHero.module.css";

type HeroSlide = {
  id: number;
  image: string;
  title: string;
  subtitle: string;
  description: string;
};

const slides: HeroSlide[] = [
  {
    id: 1,
    image: "/hero/hero-01.webp",
    title: "غدامس",
    subtitle: "جوهرة الصحراء الليبية",
    description:
      "مدينة تاريخية استثنائية تعكس العمق الحضاري والهوية العمرانية الأصيلة لليبيا.",
  },
  {
    id: 2,
    image: "/hero/hero-02.webp",
    title: "شحات",
    subtitle: "عراقة المتوسط وذاكرة الحضارة",
    description:
      "إرث أثري وثقافي يبرز ثراء ليبيا التاريخي ويجسد مكانتها كوجهة عالمية.",
  },
  {
    id: 3,
    image: "/hero/hero-03.webp",
    title: "طرابلس",
    subtitle: "مدينة الحياة والتاريخ",
    description:
      "تلتقي في طرابلس الثقافة والتراث والهوية الحضرية في مشهد سياحي متنوع ومميز.",
  },
  {
    id: 4,
    image: "/hero/hero-04.webp",
    title: "أوباري",
    subtitle: "سحر البحيرات والصحراء",
    description:
      "مشهد طبيعي فريد يجمع بين الرمال الذهبية والبحيرات الصحراوية في تجربة لا تُنسى.",
  },
  {
    id: 5,
    image: "/hero/hero-05.webp",
    title: "أكاكوس",
    subtitle: "فن الصخور وروح المغامرة",
    description:
      "وجهة صحراوية عالمية تحتضن نقوشًا صخرية نادرة وتجارب استكشاف استثنائية.",
  },
  {
    id: 6,
    image: "/hero/hero-06.webp",
    title: "رأس الهلال",
    subtitle: "جمال الطبيعة الليبية",
    description:
      "سواحل خلابة ومشاهد طبيعية مميزة تجعل من رأس الهلال مقصدًا سياحيًا واعدًا.",
  },
];

export default function PremiumHero() {
  const [activeIndex, setActiveIndex] = useState(0);

  const activeSlide = useMemo(() => slides[activeIndex], [activeIndex]);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % slides.length);
    }, 6000);

    return () => clearInterval(interval);
  }, []);

  return (
    <section className={styles.hero}>
      <div className={styles.slider}>
        {slides.map((slide, index) => (
          <div
            key={slide.id}
            className={`${styles.slide} ${
              index === activeIndex ? styles.active : ""
            }`}
          >
            <Image
              src={slide.image}
              alt={slide.title}
              fill
              priority={index === 0}
              className={styles.image}
            />
          </div>
        ))}
      </div>

      <div className={styles.contentWrap}>
        <div className={styles.content}>
          <span className={styles.kicker}>الأطلس السياحي الرقمي الوطني الليبي</span>
          <h1 className={styles.mainTitle}>
            ليبيا…
            <br />
            <span>أطلس وطني يفتح الوجهات على العالم</span>
          </h1>

          <p className={styles.mainCopy}>
            منصة وطنية متقدمة لاستكشاف الوجهات السياحية والتراث والثقافة
            والخدمات والمسارات والاستثمار والمؤشرات الجغرافية في ليبيا.
          </p>

          <div className={styles.ctaRow}>
            <a href="#sectors" className={styles.primaryBtn}>
              استكشف قطاعات الأطلس
            </a>
            <a href="#map" className={styles.secondaryBtn}>
              ابدأ بالخريطة
            </a>
          </div>

          <div className={styles.destinationBox}>
            <p className={styles.destinationLabel}>الوجهة المعروضة الآن</p>
            <h2 className={styles.destinationTitle}>{activeSlide.title}</h2>
            <p className={styles.destinationSubtitle}>{activeSlide.subtitle}</p>
            <p className={styles.destinationDescription}>
              {activeSlide.description}
            </p>
          </div>
        </div>

        <div className={styles.thumbRail}>
          {slides.map((slide, index) => (
            <button
              key={slide.id}
              className={`${styles.thumb} ${
                index === activeIndex ? styles.thumbActive : ""
              }`}
              onClick={() => setActiveIndex(index)}
              aria-label={`عرض ${slide.title}`}
              type="button"
            >
              <span className={styles.thumbNumber}>
                {String(slide.id).padStart(2, "0")}
              </span>
              <span className={styles.thumbText}>{slide.title}</span>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}