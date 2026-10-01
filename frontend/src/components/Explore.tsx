"use client";

import { useState } from "react";
import ExploreCard from "./ExploreCard";

const items = [
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

export default function Explore() {
  const [search, setSearch] = useState("");

  const filteredItems = items.filter((item) =>
    item.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <section id="explore">
      <h2>Explore MIZIZI</h2>

      <input
        type="text"
        placeholder="Search MIZIZI..."
        value={search}
        onChange={(event) => setSearch(event.target.value)}
      />

      <div className="explore-grid">
        {filteredItems.map((item) => (
          <ExploreCard
            key={item.title}
            title={item.title}
            description={item.description}
          />
        ))}
      </div>

      {filteredItems.length === 0 && (
        <p>No results found.</p>
      )}
    </section>
  );
}