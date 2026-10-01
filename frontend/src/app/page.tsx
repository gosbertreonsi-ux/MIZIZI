import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import ExploreCard from "@/components/ExploreCard";

const exploreItems = [
  {
    title: "Places",
    description: "Discover locations and their stories.",
  },
  {
    title: "Stories",
    description: "Explore culture, history and ideas.",
  },
  {
    title: "People",
    description: "Discover people connected to the world around them.",
  },
  {
    title: "Businesses",
    description: "Discover businesses and organizations.",
  },
];

export default function Home() {
  return (
    <>
      <Navbar />

      <Hero />

      <section id="explore">
        <h2>Explore MIZIZI</h2>

        <div className="explore-grid">
          {exploreItems.map((item) => (
            <ExploreCard
              key={item.title}
              title={item.title}
              description={item.description}
            />
          ))}
        </div>
      </section>
    </>
  );
}