import { assetPath } from "./assetPath";
export type AtlasPhoto = {
  id: string;
  image: string;
  title: string;
  category: string;
  description: string;
};

// V2.5 — تصحيح ربط صور الوجهات بناءً على مراجعة المستخدم للصورة المعروضة.
// تبقى الصور القديمة في أماكنها؛ نغيّر الربط والعناوين فقط، ونضيف صورة صبراتة المعتمدة.
// توثيق المواقع وحقوق نشر الصور مطلوب قبل الإطلاق العام.
export const heroSlides: AtlasPhoto[] = [
  {
    id: "leptis",
    image: assetPath("/atlas-v23/hero/sabratha.webp"),
    title: "لبدة الكبرى",
    category: "الآثار والحضارة",
    description: "المعالم الأثرية والعمارة الرومانية في لبدة الكبرى.",
  },
  {
    id: "sabratha",
    image: assetPath("/atlas-v23/hero/sabratha-approved.webp"),
    title: "صبراتة",
    category: "الآثار والتراث الساحلي",
    description: "الموقع الأثري في صبراتة بإطلالته على الساحل الليبي.",
  },
  {
    id: "cyrene",
    image: assetPath("/atlas-v23/hero/leptis-magna.webp"),
    title: "شحات (قورينا)",
    category: "الآثار والتاريخ",
    description: "المدينة الأثرية في شحات ومعالم الحضارة الإغريقية والرومانية.",
  },
  {
    id: "ghadames",
    image: assetPath("/atlas-v23/hero/ghadames.webp"),
    title: "غدامس",
    category: "التاريخ والعمارة",
    description: "العمارة الصحراوية التقليدية والهوية التراثية.",
  },
  {
    id: "tripoli",
    image: assetPath("/atlas-v23/hero/old-tripoli.webp"),
    title: "المدينة القديمة طرابلس",
    category: "التراث والثقافة",
    description: "الأفنية والأزقة والمشهد العمراني التاريخي.",
  },
  {
    id: "investment",
    image: assetPath("/atlas-v23/hero/investment.webp"),
    title: "الاستثمار والتنمية السياحية",
    category: "الاستثمار",
    description: "مشروعات التنمية العمرانية والخدمات السياحية.",
  },
  {
    id: "akakus",
    image: assetPath("/atlas-v23/hero/akakus.webp"),
    title: "أكاكوس",
    category: "الصحراء والمغامرة",
    description: "تضاريس صحراوية ومعالم طبيعية متنوعة.",
  },
  {
    id: "ubari",
    image: assetPath("/atlas-v23/hero/ubari.webp"),
    title: "بحيرات أوباري",
    category: "الطبيعة والموارد البيئية",
    description: "البحيرات والكثبان الرملية في الصحراء الليبية.",
  },
];

export const destinationCards: AtlasPhoto[] = [
  heroSlides[0], // لبدة الكبرى: الصورة التي كان عنوانها صبراتة
  heroSlides[1], // صبراتة: الصورة التي اعتمدها المستخدم
  heroSlides[2], // شحات: الصورة التي كان عنوانها لبدة الكبرى
  heroSlides[3], // غدامس
  heroSlides[4], // المدينة القديمة
  heroSlides[6], // أكاكوس
  heroSlides[7], // أوباري
  {
    id: "coast",
    image: assetPath("/atlas-v23/hero/coast.webp"),
    title: "الساحل الليبي",
    category: "الشواطئ والطبيعة",
    description: "الواجهات البحرية والمقومات الطبيعية.",
  },
];

export const featureCards: AtlasPhoto[] = [
  {
    id: "investment-feature",
    image: assetPath("/atlas-v23/sections/investment-day.webp"),
    title: "الاستثمار والتنمية السياحية",
    category: "الاستثمار",
    description: "التنمية السياحية ومشروعات الإيواء والخدمات والبنية الأساسية.",
  },
  {
    id: "folklore",
    image: assetPath("/atlas-v23/sections/folklore.webp"),
    title: "الفلكلور والموروث الشعبي",
    category: "التراث غير المادي",
    description: "الفنون الشعبية التي تعكس التنوع الثقافي الليبي.",
  },
  {
    id: "equestrian",
    image: assetPath("/atlas-v23/sections/equestrian.webp"),
    title: "الفروسية التقليدية",
    category: "الفلكلور",
    description: "مظاهر التراث والاحتفالات الشعبية.",
  },
  {
    id: "waterfall",
    image: assetPath("/atlas-v23/sections/waterfall.webp"),
    title: "الموارد الطبيعية والبيئية",
    category: "الطبيعة",
    description: "تنوع المشاهد الطبيعية والمقومات البيئية.",
  },
  {
    id: "jewelry",
    image: assetPath("/atlas-v23/sections/jewelry.webp"),
    title: "الصناعات التقليدية",
    category: "الحرف التراثية",
    description: "الحلي والمشغولات التقليدية الليبية.",
  },
];

