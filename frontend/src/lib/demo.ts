/**
 * Demo mode: mock data & utilities.
 * When demo mode is active, all API calls return mock data
 * so the app can be tested without a backend.
 *
 * Dev mode: uses the real backend with dev auth bypass.
 * When dev mode is active, calls go to the real API without Supabase auth.
 */

import type {
  StudyGuide,
  StudyGuideListItem,
  CreditStatus,
  Job,
  GuideListResponse,
  JobCreatedResponse,
  Persona,
} from "@/types";
import { extractVideoId } from "@/lib/utils";

// ── Demo Mode Detection ────────────────────────────────────────

const DEMO_COOKIE = "mindmesh-demo";
const DEV_COOKIE = "mindmesh-dev";

export function isDemoMode(): boolean {
  if (typeof window === "undefined") return false;
  return document.cookie.includes(`${DEMO_COOKIE}=true`);
}

export function isDevMode(): boolean {
  if (typeof window === "undefined") return false;
  return document.cookie.includes(`${DEV_COOKIE}=true`);
}

export function enableDemoMode() {
  document.cookie = `${DEMO_COOKIE}=true; path=/; max-age=86400; SameSite=Lax`;
}

export function enableDevMode() {
  // Clear demo cookie if set
  document.cookie = `${DEMO_COOKIE}=; path=/; max-age=0`;
  document.cookie = `${DEV_COOKIE}=true; path=/; max-age=86400; SameSite=Lax`;
}

export function disableDemoMode() {
  document.cookie = `${DEMO_COOKIE}=; path=/; max-age=0`;
  document.cookie = `${DEV_COOKIE}=; path=/; max-age=0`;
}

// ── Dev User ───────────────────────────────────────────────────

export const DEV_USER = {
  id: "dev-user-001",
  email: "dev@mindmesh.local",
  user_metadata: { full_name: "Dev User" },
  created_at: new Date().toISOString(),
};

// ── Demo User ──────────────────────────────────────────────────

export const DEMO_USER = {
  id: "demo-user-001",
  email: "demo@mindmesh.app",
  user_metadata: { full_name: "Demo User" },
  created_at: new Date().toISOString(),
};

// ── Demo Credits ───────────────────────────────────────────────

export const DEMO_CREDITS: CreditStatus = {
  credits_used: 1,
  daily_credit_limit: 3,
  credits_remaining: 2,
  tier: "free",
};

// ── Demo Study Guides ──────────────────────────────────────────

const DEMO_GUIDES: StudyGuide[] = [
  {
    id: "demo-guide-001",
    video_id: "aircAruvnKk",
    youtube_id: "aircAruvnKk",
    title: "But what is a neural network? | Deep Learning, Chapter 1",
    channel_name: "3Blue1Brown",
    thumbnail_url: null,
    persona: "beginner",
    tier: "free",
    guide_json: {
      quick_brief: {
        hook:
          "A visual, intuitive introduction to how neural networks recognize patterns by layering simple mathematical operations.",
        key_takeaways: [
          "Neural networks process data through layers of neurons, each holding an activation value between 0 and 1",
          "Each layer detects progressively more complex features — from edges to shapes to complete patterns",
          "Training adjusts thousands of weights and biases using gradient descent to minimize errors",
        ],
        clickbait_score: { score: 2, verdict: "Accurate" },
        time_saved_minutes: 12,
        highlight_quote: "Think of each neuron as holding a number — its activation — between 0 and 1.",
        highlight_quote_timestamp: "1:15",
      },
      themes: [
        {
          theme_number: 1,
          title: "What Neural Networks Actually Do",
          core_concept:
            "Neural networks take numerical inputs, process them through layers of interconnected neurons, and produce an output like classifying a handwritten digit.",
          mechanics: [
            "A neuron is just a number between 0 and 1 called an 'activation'",
            "The input layer represents raw pixel values of an image",
            "The output layer has one neuron per possible class (0-9 for digits)",
            "Hidden layers do the actual pattern recognition work",
          ],
          time_range: "0:00 - 2:30",
          analogy_or_example:
            "Think of each neuron as holding a number — its activation — between 0 and 1.",
        },
        {
          theme_number: 2,
          title: "Layers and Feature Detection",
          core_concept:
            "Each hidden layer learns to detect progressively more abstract features, from simple edges to complex shapes.",
          mechanics: [
            "First hidden layer might detect small edges and curves",
            "Second hidden layer combines edges into shapes like loops and lines",
            "Each neuron connects to all neurons in the previous layer",
            "The hope is that each layer builds on the previous one's features",
          ],
          time_range: "2:30 - 7:00",
          analogy_or_example:
            "Why would layering neurons like this lead to pattern recognition?",
        },
        {
          theme_number: 3,
          title: "Weights, Biases, and Activation Functions",
          core_concept:
            "Each connection has a weight that determines importance, and each neuron has a bias that sets its activation threshold.",
          mechanics: [
            "Weights are multiplied with activations to determine influence",
            "Positive weights excite; negative weights inhibit",
            "The bias determines how high the weighted sum needs to be before the neuron fires",
            "Sigmoid function squishes the result into the 0–1 range",
          ],
          time_range: "7:00 - 12:00",
          analogy_or_example:
            "Weights tell you what pixel pattern this neuron in the second layer is picking up on.",
        },
      ],
      quiz: [
        {
          question: "What does the activation of a neuron represent?",
          options: [
            "A number between 0 and 1 representing how 'on' the neuron is",
            "The weight of the connection to the next layer",
            "The learning rate of the network",
            "The number of inputs to the neuron",
          ],
          correct_index: 0,
          explanation:
            "Activation is a number between 0 and 1 that represents how much a neuron is 'firing' — think of it like a brightness value.",
        },
        {
          question: "What is the role of weights in a neural network?",
          options: [
            "They determine the color of each neuron",
            "They control how much influence one neuron has on another",
            "They count the number of layers in the network",
            "They measure the accuracy of the network",
          ],
          correct_index: 1,
          explanation:
            "Weights are multiplied with activations from the previous layer. Positive weights are excitatory; negative weights are inhibitory.",
        },
        {
          question: "What does the bias of a neuron control?",
          options: [
            "The speed at which the network learns",
            "How many connections a neuron has",
            "The threshold for the neuron to become meaningfully active",
            "The size of the training dataset",
          ],
          correct_index: 2,
          explanation:
            "The bias is added to the weighted sum before applying the activation function. It sets the threshold that must be exceeded for the neuron to fire.",
        },
      ],
      reflection_question:
        "If you were explaining neural networks to a 10-year-old, what real-world analogy would you use for layers detecting progressively more complex features?",
    },
    guide_markdown:
      "# Neural Networks: An Intuitive Introduction\n\nThis study guide covers the fundamentals of neural networks as explained by 3Blue1Brown in Chapter 1 of the Deep Learning series.\n\n## Overview\n\nNeural networks learn to recognize patterns by adjusting thousands of weights and biases through training. Each layer detects progressively more complex features — a simple yet powerful idea that underpins modern AI.\n\n## Key Concepts\n\n### Neurons & Activations\nEach neuron holds a number (its *activation*) between 0 and 1. The input layer takes raw pixel values; hidden layers detect features; the output layer makes the final classification.\n\n### Weights & Biases\nEvery connection between neurons has a **weight** that determines its influence. Each neuron also has a **bias** that sets the threshold for activation. Together, they control what patterns each neuron responds to.\n\n### Activation Functions\nThe **sigmoid** function (and later ReLU) squishes the weighted sum into a useful range. This non-linearity is what makes deep networks so powerful.\n\n## What's Next\nChapter 2 dives into **gradient descent** — how the network actually learns by minimizing a cost function.",
    triage_result: {
      is_educational: true,
      confidence: 0.98,
      content_type: "Computer Science / Machine Learning",
      primary_topic: "neural networks",
      estimated_complexity: "introductory",
      language: "en",
      reason: "proceed",
    },
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "demo-guide-002",
    video_id: "nLRL_NcnK-4",
    youtube_id: "nLRL_NcnK-4",
    title: "How Do CPUs Actually Work?",
    channel_name: "Branch Education",
    thumbnail_url: null,
    persona: "academic",
    tier: "free",
    guide_json: {
      quick_brief: {
        hook:
          "A detailed exploration of CPU architecture — from transistors and logic gates to instruction pipelines and cache hierarchies.",
        key_takeaways: [
          "CPUs execute instructions by combining billions of transistors into logic gates, ALUs, and control units",
          "Pipelining allows multiple instructions to be in different stages of execution simultaneously",
          "Cache memory (L1/L2/L3) bridges the massive speed gap between CPU cores and main RAM",
        ],
        clickbait_score: { score: 2, verdict: "Accurate" },
        time_saved_minutes: 10,
        highlight_quote: "At its core, a CPU is just doing the same four steps over and over — billions of times per second.",
        highlight_quote_timestamp: "5:20",
      },
      themes: [
        {
          theme_number: 1,
          title: "Transistors: The Foundation",
          core_concept:
            "Modern CPUs contain billions of transistors — tiny electrical switches that form the physical basis of all computation.",
          mechanics: [
            "A transistor acts as a tiny on/off switch controlled by voltage",
            "Combining transistors creates logic gates (AND, OR, NOT, XOR)",
            "Logic gates are the building blocks of all higher-level circuits",
            "Modern CPUs have 10+ billion transistors on a single chip",
          ],
          time_range: "0:00 - 4:15",
          analogy_or_example:
            "Everything your computer does — from loading a webpage to running a game — is built on these tiny switches.",
        },
        {
          theme_number: 2,
          title: "The Fetch-Decode-Execute Cycle",
          core_concept:
            "Every CPU instruction goes through a cycle: fetch from memory, decode the instruction, execute the operation, and write back the result.",
          mechanics: [
            "The Program Counter points to the next instruction in memory",
            "The Control Unit decodes binary instructions into control signals",
            "The ALU (Arithmetic Logic Unit) performs math and logic operations",
            "Registers provide ultra-fast temporary storage for current data",
          ],
          time_range: "4:15 - 9:30",
          analogy_or_example:
            "At its core, a CPU is just doing the same four steps over and over — billions of times per second.",
        },
        {
          theme_number: 3,
          title: "Pipelining and Performance",
          core_concept:
            "Pipelining overlaps the stages of multiple instructions, dramatically increasing throughput without increasing clock speed.",
          mechanics: [
            "A 5-stage pipeline can process 5 instructions simultaneously",
            "Pipeline hazards (data, control, structural) can cause stalls",
            "Branch prediction guesses which way an if-statement will go",
            "Out-of-order execution reorders instructions for maximum efficiency",
          ],
          time_range: "9:30 - 14:00",
          analogy_or_example:
            "It's like an assembly line — each station does its part, and a new product rolls off every cycle.",
        },
      ],
      quiz: [
        {
          question:
            "What is the fundamental building block of a CPU?",
          options: [
            "Capacitor",
            "Transistor",
            "Resistor",
            "Diode",
          ],
          correct_index: 1,
          explanation:
            "Transistors are tiny electrical switches that form logic gates, which in turn build up all the circuits in a CPU.",
        },
        {
          question: "What does the ALU do?",
          options: [
            "Stores data permanently",
            "Manages network connections",
            "Performs arithmetic and logic operations",
            "Controls the display output",
          ],
          correct_index: 2,
          explanation:
            "The Arithmetic Logic Unit performs mathematical operations (add, subtract, multiply) and logical operations (AND, OR, comparisons).",
        },
      ],
      reflection_question:
        "Compare the fetch-decode-execute cycle to a real-world process you're familiar with. What parallels do you see?",
    },
    guide_markdown:
      "# How CPUs Work: From Transistors to Execution\n\n## Overview\nThis guide breaks down CPU architecture from the ground-level transistor all the way up to pipelining and cache hierarchies.\n\n## Transistors & Logic Gates\nBillions of tiny switches form AND, OR, NOT gates — the atoms of computation.\n\n## The Execution Cycle\nEvery instruction is fetched, decoded, executed, and written back — billions of times per second.\n\n## Performance Tricks\nPipelining, branch prediction, and out-of-order execution keep the CPU running at maximum throughput.",
    triage_result: {
      is_educational: true,
      confidence: 0.95,
      content_type: "Computer Science / Hardware",
      primary_topic: "CPU architecture",
      estimated_complexity: "intermediate",
      language: "en",
      reason: "proceed",
    },
    created_at: new Date(Date.now() - 26 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "demo-guide-003",
    video_id: "Unzc731iCUY",
    youtube_id: "Unzc731iCUY",
    title: "How I Would Learn To Code (If I Could Start Over)",
    channel_name: "Traversy Media",
    thumbnail_url: null,
    persona: "practitioner",
    tier: "free",
    guide_json: {
      quick_brief: {
        hook:
          "A practitioner's roadmap for learning to code efficiently — pick one language, build projects, and avoid tutorial hell.",
        key_takeaways: [
          "Start with ONE language (JavaScript or Python) and stick with it for at least 3 months",
          "Build real projects as soon as possible — stop watching tutorials passively",
          "Focus on fundamentals (variables, functions, loops, data structures) before frameworks",
        ],
        clickbait_score: { score: 3, verdict: "Accurate" },
        time_saved_minutes: 8,
        highlight_quote: "If you're not struggling, you're not learning. Comfort is the enemy of growth.",
        highlight_quote_timestamp: "5:30",
      },
      themes: [
        {
          theme_number: 1,
          title: "Choosing Your First Language",
          core_concept:
            "The best first language is the one you'll actually use. JavaScript and Python are the most practical starting points.",
          mechanics: [
            "JavaScript: web development, most job listings, runs everywhere",
            "Python: data science, AI/ML, clean syntax, beginner-friendly",
            "Don't language-hop — depth beats breadth when starting out",
            "The concepts transfer across languages anyway",
          ],
          time_range: "0:00 - 3:45",
          analogy_or_example:
            "The biggest mistake beginners make is trying to learn five languages at once.",
        },
        {
          theme_number: 2,
          title: "Escaping Tutorial Hell",
          core_concept:
            "Watching tutorials feels productive but doesn't build real skills. The fix: build something after every concept you learn.",
          mechanics: [
            "After learning a concept, immediately build a mini-project using it",
            "Start with simple projects: calculator, to-do list, weather app",
            "Google and StackOverflow are your best friends — not more tutorials",
            "Struggling is where the real learning happens",
          ],
          time_range: "3:45 - 8:00",
          analogy_or_example:
            "If you're not struggling, you're not learning. Comfort is the enemy of growth.",
        },
        {
          theme_number: 3,
          title: "Building a Portfolio and Getting Hired",
          core_concept:
            "Three solid projects beat 100 tutorial certificates. Focus on showing what you can build.",
          mechanics: [
            "Build 3-5 quality projects that solve real problems",
            "Put everything on GitHub with clear READMEs",
            "Contribute to open source to learn professional workflows",
            "Network: Twitter, Discord communities, local meetups",
          ],
          time_range: "8:00 - 12:30",
          analogy_or_example:
            "Nobody cares about your certificates. Show them what you've built.",
        },
      ],
      quiz: [
        {
          question:
            "What is the most recommended approach for picking a first programming language?",
          options: [
            "Learn as many languages as possible simultaneously",
            "Pick one language and focus on it for at least 3 months",
            "Start with the hardest language to build discipline",
            "Only learn languages that are trending on social media",
          ],
          correct_index: 1,
          explanation:
            "Depth beats breadth when starting out. Pick one language (JavaScript or Python) and commit to it. The concepts transfer to other languages later.",
        },
        {
          question: "What is 'tutorial hell' and how do you escape it?",
          options: [
            "A website with too many tutorials — use a different site",
            "Watching tutorials without building anything — start building projects immediately",
            "Tutorials that are too difficult — watch easier ones",
            "A coding bootcamp that's too expensive — find free resources",
          ],
          correct_index: 1,
          explanation:
            "Tutorial hell is the trap of endlessly consuming content without applying it. The cure is to build something after every concept — even if it's small and imperfect.",
        },
      ],
      reflection_question:
        "What specific project would motivate you to keep coding when it gets hard? Describe it in detail.",
    },
    guide_markdown:
      "# Learn to Code: A Practical Roadmap\n\n## The Plan\n1. **Pick one language** (JS or Python)\n2. **Learn fundamentals** — variables, functions, loops, arrays, objects\n3. **Build projects immediately** — stop passive consuming\n4. **Level up** — add a framework (React, Django, etc.)\n5. **Ship and share** — GitHub, portfolio site, open source\n\n## Action Items\n- [ ] Set up your dev environment today\n- [ ] Complete one fundamentals course this week\n- [ ] Build your first mini-project by end of week 2\n- [ ] Start your portfolio project by month 2",
    triage_result: {
      is_educational: true,
      confidence: 0.88,
      content_type: "Career / Programming",
      primary_topic: "learning to code",
      estimated_complexity: "introductory",
      language: "en",
      reason: "proceed",
    },
    created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
  },
];

// ── Demo API Functions ─────────────────────────────────────────

export function demoGetCredits(): CreditStatus {
  return { ...DEMO_CREDITS };
}

export function demoGetGuides(
  page: number,
  perPage: number,
  search?: string,
  persona?: Persona
): GuideListResponse {
  // Combine static demo guides with dynamically created ones (newest first)
  const allGuides = [...Array.from(dynamicGuides.values()).reverse(), ...DEMO_GUIDES];
  let filtered = [...allGuides];

  if (search) {
    const q = search.toLowerCase();
    filtered = filtered.filter(
      (g) =>
        g.title.toLowerCase().includes(q) ||
        g.channel_name.toLowerCase().includes(q)
    );
  }

  if (persona) {
    filtered = filtered.filter((g) => g.persona === persona);
  }

  const start = (page - 1) * perPage;
  const guides: StudyGuideListItem[] = filtered
    .slice(start, start + perPage)
    .map((g) => ({
      id: g.id,
      video_id: g.video_id,
      title: g.title,
      channel_name: g.channel_name,
      thumbnail_url: g.thumbnail_url,
      persona: g.persona,
      tier: g.tier,
      created_at: g.created_at,
    }));

  return {
    guides,
    total: filtered.length,
    page,
    per_page: perPage,
  };
}

export function demoGetGuide(guideId: string): StudyGuide | null {
  // Check static demo guides first, then dynamically created ones
  return DEMO_GUIDES.find((g) => g.id === guideId) ?? dynamicGuides.get(guideId) ?? null;
}

export function demoCreateGuide(url: string, persona: Persona): JobCreatedResponse {
  const videoId = extractVideoId(url) || "dQw4w9WgXcQ";
  const guideId = `demo-guide-${Date.now()}`;
  const jobId = `demo-job-${Date.now()}`;

  // Create a dynamic guide from the pasted URL
  const personaLabels: Record<string, string> = {
    beginner: "Beginner-Friendly",
    academic: "Academic Deep-Dive",
  };

  const newGuide: StudyGuide = {
    id: guideId,
    video_id: videoId,
    youtube_id: videoId,
    title: `Study Guide — ${videoId}`,
    channel_name: "YouTube Creator",
    thumbnail_url: null,
    persona,
    tier: "free",
    guide_json: {
      // quick_brief: {
      //   hook: `A ${personaLabels[persona].toLowerCase()} study guide generated from your YouTube video.`,
      //   key_takeaways: [
      //     "This is a demo guide — paste any YouTube URL to see the flow in action",
      //     "In production, MindMesh uses AI to extract real insights from the video",
      //     "Choose a persona (beginner / academic / practitioner) to tailor the output",
      //   ],
      //   clickbait_score: { score: 1, verdict: "Accurate" },
      //   time_saved_minutes: 10,
      //   highlight_quote: "Switch to Dev mode to generate real AI-powered study guides!",
      //   highlight_quote_timestamp: "0:00",
      // },
      themes: [
        {
          theme_number: 1,
          title: "How MindMesh Works",
          core_concept:
            "MindMesh fetches the transcript, triages the content, and generates a structured study guide using AI — tailored to your selected learning persona.",
          mechanics: [
            "Transcripts are extracted automatically via YouTube or Whisper",
            "An AI triage step checks whether the video is educational",
            `Your \"${personaLabels[persona]}\" persona shapes the depth and tone`,
            "The final guide includes themes, quizzes, and reflection prompts",
          ],
          time_range: "0:00 - end",
          analogy_or_example:
            "Switch to Dev mode to generate real AI-powered study guides!",
        },
      ],
      quiz: [
        {
          question: "What does MindMesh use to generate study guides?",
          options: [
            "Random text generation",
            "AI analysis of video transcripts",
            "Manual human review",
            "Screenshot analysis",
          ],
          correct_index: 1,
          explanation:
            "MindMesh extracts the video transcript and uses AI (GPT-4) to produce structured, persona-tailored study guides.",
        },
      ],
      reflection_question:
        "What kind of videos would benefit most from an AI-generated study guide?",
    },
    guide_markdown:
      `# Study Guide — ${videoId}\n\n` +
      `**Persona:** ${personaLabels[persona]}\n\n` +
      `## This is a Demo Guide\n\n` +
      `This guide was generated in **demo mode** using sample data.\n\n` +
      `To get **real AI-powered guides**, visit \`/dev\` to switch to Dev mode,\n` +
      `then paste a YouTube URL and the AI will analyze the actual video content.\n\n` +
      `## Video\n\n` +
      `YouTube video ID: \`${videoId}\``,
    triage_result: {
      is_educational: true,
      confidence: 0.85,
      content_type: "Demo / Preview",
      primary_topic: "demo",
      estimated_complexity: persona === "beginner" ? "introductory" : persona === "academic" ? "advanced" : "intermediate",
      language: "en",
      reason: "proceed",
    },
    created_at: new Date().toISOString(),
  };

  // Store the guide in our dynamic guides list
  dynamicGuides.set(guideId, newGuide);

  // Map this job ID → guide ID so demoGetJobStatus knows what to return
  jobToGuideMap.set(jobId, guideId);

  return {
    job_id: jobId,
    message: "Demo job created",
  };
}

// Maps job IDs to their created guide IDs
const jobToGuideMap: Map<string, string> = new Map();

// Stores dynamically created demo guides
const dynamicGuides: Map<string, StudyGuide> = new Map();

// Simulated job progress — returns the next state each time
const jobProgress: Map<string, number> = new Map();

export function demoGetJobStatus(jobId: string): Job {
  const step = jobProgress.get(jobId) ?? 0;
  jobProgress.set(jobId, step + 1);

  const stages: { progress: number; current_step: string; status: Job["status"] }[] = [
    { progress: 5, current_step: "validating_video", status: "processing" },
    { progress: 15, current_step: "fetching_transcript", status: "processing" },
    { progress: 30, current_step: "checking_credits", status: "processing" },
    { progress: 50, current_step: "analyzing_content", status: "processing" },
    { progress: 75, current_step: "generating_guide", status: "processing" },
    { progress: 90, current_step: "saving_results", status: "processing" },
    { progress: 100, current_step: "done", status: "completed" },
  ];

  const current = stages[Math.min(step, stages.length - 1)];
  const isComplete = current.status === "completed";

  // Look up the guide ID for this specific job
  const resultId = isComplete ? (jobToGuideMap.get(jobId) ?? "demo-guide-001") : null;

  return {
    job_id: jobId,
    status: current.status,
    progress: current.progress,
    current_step: current.current_step,
    error_message: null,
    result_id: resultId,
    created_at: new Date().toISOString(),
    completed_at: isComplete ? new Date().toISOString() : null,
  };
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function demoDeleteGuide(_guideId: string): void {
  // no-op in demo
}
