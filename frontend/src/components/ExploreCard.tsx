type ExploreCardProps = {
  title: string;
  description: string;
};

export default function ExploreCard({
  title,
  description,
}: ExploreCardProps) {
  return (
    <article>
      <h3>{title}</h3>
      <p>{description}</p>
    </article>
  );
}