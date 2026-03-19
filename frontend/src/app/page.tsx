import Link from "next/link";
import {
  Brain,
  BookOpen,
  Zap,
  Shield,
  Users,
  BarChart3,
  PenLine,
  CheckCircle2,
  ArrowRight,
  Star,
  Play,
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#FAFAF9]">
      {/* Nav */}
      <nav className="flex items-center justify-between max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
        <div className="flex items-center gap-2">
          <Brain className="w-7 h-7 text-indigo-600" />
          <span className="font-bold text-lg text-gray-900">MindMesh</span>
        </div>
        <div className="flex items-center gap-4">
          <Link
            href="/pricing"
            className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors hidden sm:block"
          >
            Pricing
          </Link>
          <Link
            href="/login"
            className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
          >
            Sign In
          </Link>
          <Link
            href="/dev"
            className="text-sm font-medium bg-emerald-600 text-white px-4 py-2 rounded-lg hover:bg-emerald-700 transition-colors"
          >
            Dev Mode
          </Link>
          <Link
            href="/demo"
            className="text-sm font-medium bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Try Demo
          </Link>
        </div>
      </nav>

      {/* Hero — more focused, less generic */}
      <section className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-8 text-center relative">
        {/* Subtle gradient glow */}
        <div className="absolute top-12 left-1/2 -translate-x-1/2 w-96 h-96 bg-gradient-to-r from-indigo-200 via-purple-200 to-pink-200 rounded-full blur-3xl opacity-30 pointer-events-none" />
        <h1 className="relative text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 leading-[1.1] tracking-tight mb-6">
          Paste a YouTube link.
          <br />
          <span className="text-indigo-600">Get a study guide.</span>
        </h1>
        <p className="text-lg text-gray-500 max-w-xl mx-auto mb-10">
          MindMesh watches the video for you, then builds a structured guide
          with key themes, quizzes, and reflection prompts — tailored to how you
          learn.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/demo"
            className="inline-flex items-center gap-2 bg-indigo-600 text-white px-8 py-3.5 rounded-xl text-base font-semibold hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-200"
          >
            Try Demo
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/dev"
            className="inline-flex items-center gap-2 bg-emerald-600 text-white px-8 py-3.5 rounded-xl text-base font-semibold hover:bg-emerald-700 transition-colors shadow-lg shadow-emerald-200"
          >
            Dev Mode
            <Zap className="w-4 h-4" />
          </Link>
          <Link
            href="/signup"
            className="inline-flex items-center gap-2 text-gray-600 px-8 py-3.5 rounded-xl text-base font-medium hover:bg-gray-100 transition-colors"
          >
            Create Account
          </Link>
        </div>
      </section>

      {/* Interactive Demo Preview — looks like the real app */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white rounded-2xl border border-gray-200 shadow-xl shadow-gray-200/50 overflow-hidden">
          {/* Fake browser bar */}
          <div className="flex items-center gap-2 px-4 py-3 bg-gray-50 border-b border-gray-200">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-gray-300" />
              <div className="w-3 h-3 rounded-full bg-gray-300" />
              <div className="w-3 h-3 rounded-full bg-gray-300" />
            </div>
            <div className="flex-1 mx-4 bg-white rounded-md border border-gray-200 px-3 py-1 text-xs text-gray-400">
              mindmesh.app/dashboard
            </div>
          </div>

          <div className="p-6 sm:p-8">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
              {/* Left: input area (3 cols) */}
              <div className="md:col-span-3 space-y-4">
                <div>
                  <p className="text-xs text-gray-400 font-medium mb-2 uppercase tracking-wider">
                    YouTube URL
                  </p>
                  <div className="flex items-center bg-gray-50 rounded-xl border border-gray-200 px-4 py-3">
                    <Play className="w-4 h-4 text-red-500 mr-2 flex-shrink-0" />
                    <span className="text-sm text-gray-700 truncate">
                      https://youtube.com/watch?v=aircAruvnKk
                    </span>
                  </div>
                </div>
                <div className="flex flex-wrap gap-3 pb-2 pt-1 border-b border-white/5">
                  <span className="text-xs font-semibold uppercase tracking-wider text-gray-400 mr-2 mt-2">
                    1. CHOOSE PERSONA:
                  </span>
                  <div className="flex gap-2">
                    {["🌱 Beginner", "🎓 Academic"].map(
                      (persona, i) => (
                        <div
                          key={persona}
                          className={`px-3 py-1.5 rounded-full text-sm flex items-center gap-1.5 transition-colors cursor-pointer ${i === 0
                              ? "bg-indigo-600 text-white font-medium shadow-sm hover:bg-indigo-700"
                              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                            }`}
                        >
                          {persona}
                        </div>
                      )
                    )}
                  </div>
                </div>
                <div className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold px-6 py-3 rounded-xl text-center transition-colors cursor-default">
                  Generate Study Guide
                </div>
              </div>

              {/* Right: output preview (2 cols) */}
              <div className="md:col-span-2 space-y-3">
                <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-4 border border-indigo-100">
                  <div className="flex items-center gap-2 mb-2">
                    <Zap className="w-3.5 h-3.5 text-indigo-600" />
                    <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">
                      Quick Brief
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 leading-relaxed">
                    A visual introduction to how neural networks recognize
                    patterns by layering simple math operations.
                  </p>
                </div>
                <div className="space-y-1.5">
                  {[
                    { label: "3 Key Themes", icon: "🧩" },
                    { label: "3 Quiz Questions", icon: "📝" },
                    { label: "Reflection Prompts", icon: "💭" },
                    { label: "Timestamps & Quotes", icon: "⏱️" },
                  ].map((item) => (
                    <div
                      key={item.label}
                      className="flex items-center gap-2 text-xs bg-white border border-gray-100 rounded-lg px-3 py-2 text-gray-600"
                    >
                      <span>{item.icon}</span>
                      {item.label}
                      <CheckCircle2 className="w-3 h-3 text-green-500 ml-auto" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features — compact grid */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center mb-10">
          <h2 className="text-2xl font-bold text-gray-900 mb-3">
            What&apos;s inside every guide
          </h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <FeatureCard
            icon={<Users className="w-5 h-5 text-indigo-600" />}
            title="Tailored to your learning style"
            description="Beginner or Academic — each gets a different guide."
          />
          <FeatureCard
            icon={<BarChart3 className="w-5 h-5 text-amber-500" />}
            title="Theme Blocks"
            description="Collapsible sections with key points, timestamps, and quotes."
          />
          <FeatureCard
            icon={<Shield className="w-5 h-5 text-green-600" />}
            title="Smart Triage"
            description="AI filters out non-educational content automatically."
          />
          <FeatureCard
            icon={<BookOpen className="w-5 h-5 text-purple-500" />}
            title="Quizzes"
            description="Multiple-choice questions with explanations."
          />
          <FeatureCard
            icon={<PenLine className="w-5 h-5 text-orange-500" />}
            title="Reflection"
            description="Guided writing prompts to internalize the material."
          />
        </div>
      </section>

      {/* How it works — simple numbered steps */}
      <section className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-10">
          Three steps. That&apos;s it.
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
          <Step
            number="1"
            title="Paste a YouTube URL"
            description="Any public video with English captions works."
          />
          <Step
            number="2"
            title="Three learning personas."
            description="Beginner or Academic — we adapt the guide to you."
          />
          <Step
            number="3"
            title="Study smarter"
            description="Get themes, quizzes, and reflection prompts in seconds."
          />
        </div>
      </section>

      {/* Social Proof — compact */}
      <section className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white rounded-2xl border border-gray-200 p-6 sm:p-8">
          <div className="flex items-center justify-center gap-1 mb-6">
            {[1, 2, 3, 4, 5].map((i) => (
              <Star
                key={i}
                className="w-4 h-4 fill-amber-400 text-amber-400"
              />
            ))}
            <span className="ml-2 text-sm text-gray-500">from early users</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              {
                quote: "I use MindMesh for every lecture recording. Saves me hours.",
                name: "Alex K.",
                role: "CS Student",
              },
              {
                quote: "The quiz feature actually tests whether I understood the material.",
                name: "Priya M.",
                role: "Self-learner",
              },
              {
                quote: "The Academic persona is perfect for diving deep into industry talks. Love it.",
                name: "Aisha K.",
                role: "Product Manager",
              },
            ].map((t) => (
              <div key={t.name} className="text-center">
                <p className="text-sm text-gray-600 leading-relaxed mb-3">
                  &ldquo;{t.quote}&rdquo;
                </p>
                <p className="text-xs font-medium text-gray-900">{t.name}</p>
                <p className="text-xs text-gray-400">{t.role}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-3">
          Ready to try it?
        </h2>
        <p className="text-gray-500 mb-8 max-w-md mx-auto">
          No sign-up required. See your first study guide in 30 seconds.
        </p>
        <Link
          href="/demo"
          className="inline-flex items-center gap-2 bg-indigo-600 text-white px-8 py-3.5 rounded-xl text-base font-semibold hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-200"
        >
          Launch Demo
          <ArrowRight className="w-4 h-4" />
        </Link>
      </section>

      {/* Footer */}
      <footer className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 border-t border-gray-100">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-indigo-600" />
            <span className="font-semibold text-gray-900">MindMesh</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-gray-400">
            <Link href="/pricing" className="hover:text-gray-600 transition-colors">
              Pricing
            </Link>
            <Link href="/login" className="hover:text-gray-600 transition-colors">
              Sign In
            </Link>
            <Link href="/demo" className="hover:text-gray-600 transition-colors">
              Demo
            </Link>
          </div>
          <p className="text-sm text-gray-400">
            &copy; {new Date().getFullYear()} MindMesh
          </p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-sm hover:border-gray-300 transition-all duration-200">
      <div className="flex items-center gap-2.5 mb-2">
        <div className="w-8 h-8 bg-gray-50 rounded-lg flex items-center justify-center flex-shrink-0">
          {icon}
        </div>
        <h3 className="font-semibold text-gray-900 text-sm">{title}</h3>
      </div>
      <p className="text-xs text-gray-500 leading-relaxed">{description}</p>
    </div>
  );
}

function Step({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div>
      <div className="w-9 h-9 bg-indigo-600 text-white rounded-full flex items-center justify-center mx-auto mb-3 text-sm font-bold">
        {number}
      </div>
      <h3 className="font-semibold text-gray-900 text-sm mb-1">{title}</h3>
      <p className="text-xs text-gray-500">{description}</p>
    </div>
  );
}
