import React from "react";
import styles from "./LoadingSkeleton.module.css";

export const LoadingSkeleton: React.FC = () => {
  return (
    <div className={styles.wrapper}>
      <div className={styles.bannerSkeleton}></div>

      <div className={styles.titleSkeleton}></div>

      <div className={styles.grid}>
        {[1, 2, 3, 4, 5, 6].map((n) => (
          <div key={n} className={styles.cardSkeleton}>
            <div className={styles.imageSkeleton}></div>
            <div className={styles.contentSkeleton}>
              <div className={styles.lineLong}></div>
              <div className={styles.lineShort}></div>
              <div className={styles.lineTags}></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
