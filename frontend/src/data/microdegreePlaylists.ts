export interface Playlist {
  title: string;
  url: string;
  category: string;
}

export const microdegreePlaylists: Playlist[] = [
  // Cloud & DevOps
  {
    title: "Cloud Career Playlist | MicroDegree",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "Cloud Engineer",
  },
  {
    title: "AWS Full Course in Kannada",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "Cloud Engineer",
  },
  {
    title: "Azure Masterclass",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "Cloud Engineer",
  },
  {
    title: "DevOps in Kannada 2024",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "DevOps Engineer",
  },
  {
    title: "Master DevOps in 6 Hours – Live Series",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "DevOps Engineer",
  },
  {
    title: "Learn Docker in 3 Hours",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "DevOps Engineer",
  },
  {
    title: "Learn Jenkins in 4 Hours",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "DevOps Engineer",
  },
  {
    title: "Learn Git in 4 Hours",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "DevOps Engineer",
  },

  // AI & Data Science
  {
    title: "Generative AI Playlist | MicroDegree",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "AI Engineer",
  },
  {
    title: "Artificial Intelligence & Machine Learning",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "AI Engineer",
  },
  {
    title: "Data Science for Beginners",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "Data Scientist",
  },

  // Software Development
  {
    title: "Python in Kannada | MicroDegree",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "Software Engineer",
  },
  {
    title: "Java in Kannada | MicroDegree",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "Software Engineer",
  },
  {
    title: "React in Kannada",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "Frontend Developer",
  },
  {
    title: "JavaScript for Beginners in Kannada",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "Frontend Developer",
  },
  {
    title: "HTML & CSS Full Course in Kannada",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "Frontend Developer",
  },
  {
    title: "MERN Stack",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "Full Stack Developer",
  },

  // Computer Science Fundamentals
  {
    title: "Data Structures & Algorithm in Kannada",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "Software Engineer",
  },
  {
    title: "Problems on Data Structures & Algorithm",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "Software Engineer",
  },

  // Testing & Automation
  {
    title: "Manual Testing",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "QA Engineer",
  },
  {
    title: "Software Testing",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "QA Engineer",
  },
  {
    title: "Selenium Automation Testing",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "Automation Engineer",
  },

  // Career & Guidance
  {
    title: "Tech Roles",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "General",
  },
  {
    title: "Learner Success Story",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "General",
  },
  {
    title: "MicroDegree Podcast",
    url: "https://www.youtube.com/@MicroDegree/playlists",
    category: "General",
  },
];

export const DEFAULT_PLAYLISTS = microdegreePlaylists.slice(0, 6);
