const { PrismaClient } = require("@prisma/client");

const prisma = new PrismaClient();

async function main() {
  await prisma.exploreItem.createMany({
    data: [
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
        description:
          "Discover people connected to the world around them.",
      },
      {
        title: "Businesses",
        description:
          "Discover businesses and organizations.",
      },
    ],
  });
}

main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (error) => {
    console.error(error);
    await prisma.$disconnect();
    process.exit(1);
  });