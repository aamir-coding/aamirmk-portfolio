import desktop from "./art/field-desktop.webp";
import mobile from "./art/field-mobile.webp";
import tablet from "./art/field-tablet.webp";

export function HeroArt() {
  return (
    <picture className="portfolio-hero-art" aria-hidden="true">
      <source media="(max-width: 40rem)" srcSet={mobile} />
      <source media="(max-width: 70rem)" srcSet={tablet} />
      <img
        src={desktop}
        alt=""
        width={1440}
        height={548}
        decoding="async"
        fetchPriority="high"
        onError={event => { event.currentTarget.hidden = true; }}
        onLoad={event => { event.currentTarget.hidden = false; }}
      />
    </picture>
  );
}
