const express = require("express");
const cors = require("cors");

const app = express();
const PORT = 5000;

app.use(cors());
app.use(express.json());

const exploreItems = [
  {
    id: 1,
    title: "Places",
    description: "Discover locations and their stories.",
  },
  {
    id: 2,
    title: "Stories",
    description: "Explore culture, history and ideas.",
  },
  {
    id: 3,
    title: "People",
    description: "Discover people connected to the world around them.",
  },
  {
    id: 4,
    title: "Businesses",
    description: "Discover businesses and organizations.",
  },
];

app.get("/api/explore", (req, res) => {
  res.json(exploreItems);
});

app.get("/api/health", (req, res) => {
  res.json({
    status: "ok",
    service: "MIZIZI API",
  });
});

app.listen(PORT, () => {
  console.log(`MIZIZI API running on http://localhost:${PORT}`);
});