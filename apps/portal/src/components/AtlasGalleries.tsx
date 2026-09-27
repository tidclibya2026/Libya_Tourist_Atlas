import Image from "next/image";
import { destinationCards, featureCards, type AtlasPhoto } from "../data/atlasMedia";
import styles from "./AtlasGalleries.module.css";

function PhotoCard({ item }: { item: AtlasPhoto }) {
  return (
    <article className={styles.card}>
      <div className={styles.imageWrap}>
        <Image src={item.image} alt={item.title} fill sizes="(max-width:700px) 100vw, (max-width:1100px) 50vw, 33vw" unoptimized className={styles.image} />
      </div>
      <div className={styles.text}>
        <span>{item.category}</span><h3>{item.title}</h3><p>{item.description}</p>
      </div>
    </article>
  );
}

export default function AtlasGalleries() {
  return (
    <>
      <section id="destinations" className={styles.section}>
        <div className={styles.heading}><span>اكتشف ليبيا</span><h2>وجهات سياحية متنوعة</h2><p>من الآثار والمدن التاريخية إلى الصحراء والسواحل.</p></div>
        <div className={styles.grid}>{destinationCards.map((item) => <PhotoCard key={item.id} item={item} />)}</div>
      </section>
      <section id="experiences" className={`${styles.section} ${styles.tinted}`}>
        <div className={styles.heading}><span>ما وراء الوجهات</span><h2>الثقافة والطبيعة والاستثمار</h2><p>الموروث الشعبي، والموارد البيئية، والحرف، وآفاق التنمية السياحية.</p></div>
        <div className={styles.grid}>{featureCards.map((item) => <PhotoCard key={item.id} item={item} />)}</div>
      </section>
    </>
  );
}
