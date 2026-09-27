"use client";
import { useMemo, useState } from "react";
import PremiumHero from "../components/PremiumHero";
import AtlasGalleries from "../components/AtlasGalleries";
import styles from "./page.module.css";

type Sector = { name: string; group: "استكشف" | "خطط" | "اعرف" | "الإدارة"; desc: string };
const sectors: Sector[] = [
  { name: "الوجهات السياحية", group: "استكشف", desc: "المعالم والمدن والوجهات الوطنية" },
  { name: "الخرائط والمسارات", group: "خطط", desc: "الاستكشاف الجغرافي والمسارات السياحية" },
  { name: "الأطلس الإحصائي", group: "اعرف", desc: "المؤشرات السياحية والخرائط الموضوعية" },
  { name: "الاستثمار السياحي", group: "خطط", desc: "الفرص والمشروعات الاستثمارية المعتمدة" },
  { name: "الإيواء السياحي", group: "خطط", desc: "الفنادق والمنتجعات والقرى السياحية" },
  { name: "المعرفة والذكاء الاصطناعي", group: "اعرف", desc: "المعلومات السياحية والمساعد المعرفي" },
  { name: "التراث والثقافة", group: "استكشف", desc: "المدن التاريخية والمتاحف والموروث الشعبي" },
  { name: "الخدمات والنقل السياحي", group: "خطط", desc: "الخدمات وشركات النقل ومراكز المعلومات" },
  { name: "المرشدون السياحيون", group: "خطط", desc: "المرشدون المعتمدون والتخصصات واللغات" },
  { name: "الطعام والشراب", group: "استكشف", desc: "المطاعم والمقاهي والمأكولات التقليدية" },
  { name: "الأحداث السياحية", group: "استكشف", desc: "المهرجانات والفعاليات والمؤتمرات" },
  { name: "الدليل السياحي المتكامل", group: "اعرف", desc: "دليل المواقع والخدمات والمعلومات" },
  { name: "إدارة الأطلس", group: "الإدارة", desc: "المراجعة والاعتماد والحوكمة" },
  { name: "المنتزهات والحدائق", group: "استكشف", desc: "المنتزهات والحدائق والمساحات الطبيعية" },
  { name: "الترفيه والأنشطة السياحية", group: "استكشف", desc: "الأنشطة البحرية والعائلية والصحراوية" },
];
const filters = ["الكل", "استكشف", "خطط", "اعرف", "الإدارة"] as const;

export default function Home() {
  const [query, setQuery] = useState("");
  const [group, setGroup] = useState<(typeof filters)[number]>("الكل");
  const [selected, setSelected] = useState<Sector | null>(null);
  const visible = useMemo(() => sectors.filter((sector) => (group === "الكل" || sector.group === group) && (`${sector.name} ${sector.desc}`).includes(query.trim())), [query, group]);
  return (
    <div className={styles.shell} dir="rtl">
      <header className={styles.header}>
        <a href="#top" className={styles.brand}><span className={styles.brandMark}>LY</span><span><strong>الأطلس السياحي الرقمي الوطني</strong><small>LIBYA DIGITAL TOURISM ATLAS</small></span></a>
        <nav className={styles.nav} aria-label="القائمة الرئيسية"><a href="#destinations">الوجهات</a><a href="#experiences">الثقافة والطبيعة</a><a href="#sectors">القطاعات</a><a href="#map">الخريطة</a></nav>
        <span className={styles.language}>العربية</span>
      </header>
      <main id="top">
        <PremiumHero />
        <div className={styles.strip}><div><strong>15</strong><span>وحدة وظيفية</span></div><div><strong>GIS</strong><span>خرائط وطنية</span></div><div><strong>ليبيا</strong><span>آثار وطبيعة وتراث</span></div><div><strong>ATLAS</strong><span>بوابة موحدة</span></div></div>
        <AtlasGalleries />
        <section id="sectors" className={styles.sectors}>
          <div className={styles.sectionHeading}><span>دليل الأطلس</span><h2>القطاعات الخمسة عشر</h2><p>تصفّح القطاعات التي ستُربط تدريجياً بالسجلات المكانية المعتمدة.</p></div>
          <div className={styles.tools}><div className={styles.filters}>{filters.map((item) => <button type="button" key={item} className={group === item ? styles.filterActive : styles.filter} aria-pressed={group === item} onClick={() => setGroup(item)}>{item}</button>)}</div><label className={styles.search}><span>بحث</span><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="ابحث في قطاعات الأطلس" /></label></div>
          <div className={styles.sectorGrid}>{visible.map((item, index) => <button type="button" key={item.name} className={styles.sectorCard} onClick={() => setSelected(item)}><span className={styles.number}>{String(index + 1).padStart(2, "0")}</span><strong>{item.name}</strong><small>{item.desc}</small><em>التفاصيل ←</em></button>)}</div>
          {visible.length === 0 && <p>لا توجد قطاعات مطابقة للبحث.</p>}
          {selected && <div className={styles.detail}><button type="button" onClick={() => setSelected(null)} aria-label="إغلاق">×</button><span>{selected.group}</span><h3>{selected.name}</h3><p>{selected.desc}</p><p>تُتاح البيانات بعد مراجعتها واعتماد نشرها.</p></div>}
        </section>
        <section id="map" className={styles.map}><span>GIS · NATIONAL EXPLORER</span><h2>الخريطة السياحية الوطنية</h2><p>يُربط المستكشف بالطبقات المنشورة والمعتمدة من قاعدة GIS الوطنية، دون تحميل البيانات غير المجازة.</p><div className={styles.mapPlaceholder}><strong>المستكشف الجغرافي</strong><small>قيد تجهيز الاتصال بالخدمات المكانية المعتمدة</small></div></section>
      </main>
      <footer className={styles.footer}><strong>الأطلس السياحي الرقمي الوطني الليبي</strong><span>مركز المعلومات والتوثيق السياحي · 2026</span><span>نسخة التطوير V2.3</span></footer>
    </div>
  );
}
