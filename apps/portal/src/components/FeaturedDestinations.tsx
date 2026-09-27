import Image from "next/image";
import media from "../data/atlasMedia.json";
import styles from "./FeaturedDestinations.module.css";

export default function FeaturedDestinations() {
  return (
    <section id="featured" className={styles.section} aria-labelledby="featured-title">
      <div className={styles.heading}>
        <div><span className={styles.eyebrow}>اكتشف تنوع ليبيا</span><h2 id="featured-title">وجهات وتجارب مختارة</h2></div>
        <p>الآثار والتاريخ والثقافة والشواطئ والطبيعة والاستثمار، ضمن تجربة استكشاف موحدة.</p>
      </div>
      <div className={styles.grid}>
        {media.featured.map((item, index) => (
          <article key={`${item.src}-${index}`} className={styles.card}>
            <div className={styles.imageWrap}>
              <Image src={item.src} alt={item.title} fill quality={85} unoptimized sizes="(max-width:700px) 100vw, (max-width:1080px) 50vw, 33vw" className={styles.photo}/>
            </div>
            <div className={styles.body}><span>{item.category}</span><h3>{item.title}</h3><p>{item.subtitle}</p></div>
          </article>
        ))}
      </div>
      <p className={styles.provenance}>تعتمد صور الوجهات المنشورة على الملفات المختارة من مكتبة المشروع. تُراجع هوية كل صورة وحقوق نشرها قبل الإطلاق العام.</p>
    </section>
  );
}
