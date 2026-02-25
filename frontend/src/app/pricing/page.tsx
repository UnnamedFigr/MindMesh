import Link from "next/link";
import {
  Brain,
  Check,
  Zap,
  Crown,
  BookOpen,
  Target,
  Sparkles,
} from "lucide-react";

const PLANS = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    description: "Get started with basic study guides",
    cta: "Get Started",
    ctaHref: "/signup",
    features: [
      "3 study guides per day",
      "All 3 learning personas",
      "Markdown study guides",
      "YouTube URL validation",
      "Guide library & search",
    ],
    highlighted: false,
    icon: BookOpen,
  },
  {
    name: "Pro",
    price: "$9.99",
    period: "/month",
    description: "Unlock interactive learning features",
    cta: "Start Pro Trial",
    ctaHref: "/signup?plan=pro",
    features: [
      "15 study guides per day",
      "All Free features",
      "Interactive knowledge quizzes",
      "Reflection prompts & journal",
      "Web of Associations",
      "Priority processing",
      "Email support",
    ],
    highlighted: true,
    icon: Crown,
  },
];

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="flex items-center justify-between max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
        <Link href="/" className="flex items-center gap-2">
          <Brain className="w-7 h-7 text-indigo-600" />
          <span className="font-bold text-lg text-gray-900">MindMesh</span>
        </Link>
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="text-sm font-medium text-gray-600 hover:text-gray-900"
          >
            Sign In
          </Link>
          <Link
            href="/signup"
            className="text-sm font-medium bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Header */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-12 text-center">
        <div className="inline-flex items-center gap-2 bg-indigo-50 text-indigo-700 rounded-full px-4 py-1.5 text-sm font-medium mb-6">
          <Sparkles className="w-4 h-4" />
          Simple Pricing
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
          Choose your plan
        </h1>
        <p className="text-lg text-gray-500 max-w-xl mx-auto">
          Start for free, upgrade when you need more study guides and
          interactive learning features.
        </p>
      </section>

      {/* Plans */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {PLANS.map((plan) => {
            const Icon = plan.icon;
            return (
              <div
                key={plan.name}
                className={`relative rounded-2xl border-2 p-8 flex flex-col ${
                  plan.highlighted
                    ? "border-indigo-500 shadow-xl shadow-indigo-100"
                    : "border-gray-200"
                }`}
              >
                {plan.highlighted && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <span className="bg-indigo-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
                      Most Popular
                    </span>
                  </div>
                )}

                <div className="flex items-center gap-3 mb-4">
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                      plan.highlighted
                        ? "bg-indigo-100 text-indigo-600"
                        : "bg-gray-100 text-gray-600"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">
                      {plan.name}
                    </h3>
                    <p className="text-sm text-gray-500">{plan.description}</p>
                  </div>
                </div>

                <div className="flex items-baseline gap-1 mb-6">
                  <span className="text-4xl font-bold text-gray-900">
                    {plan.price}
                  </span>
                  <span className="text-gray-500 text-sm">{plan.period}</span>
                </div>

                <ul className="space-y-3 mb-8 flex-1">
                  {plan.features.map((feature) => (
                    <li
                      key={feature}
                      className="flex items-center gap-2.5 text-sm text-gray-700"
                    >
                      <Check
                        className={`w-4 h-4 flex-shrink-0 ${
                          plan.highlighted
                            ? "text-indigo-600"
                            : "text-gray-400"
                        }`}
                      />
                      {feature}
                    </li>
                  ))}
                </ul>

                <Link
                  href={plan.ctaHref}
                  className={`w-full inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold transition-colors ${
                    plan.highlighted
                      ? "bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg shadow-indigo-200"
                      : "bg-gray-100 text-gray-900 hover:bg-gray-200"
                  }`}
                >
                  {plan.highlighted && <Zap className="w-4 h-4" />}
                  {plan.cta}
                </Link>
              </div>
            );
          })}
        </div>

        {/* FAQ */}
        <div className="mt-20 max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">
            Frequently Asked Questions
          </h2>
          <div className="space-y-6">
            {[
              {
                q: "What counts as a credit?",
                a: "Each study guide generation uses 1 credit, regardless of video length. Credits reset daily at midnight UTC.",
              },
              {
                q: "Can I cancel anytime?",
                a: "Yes! Cancel your Pro subscription anytime with no penalties. You'll keep Pro features until the end of your billing period.",
              },
              {
                q: "What video formats are supported?",
                a: "Any public YouTube video with captions (manual or auto-generated). We support videos up to 4 hours long.",
              },
              {
                q: "How does the Web of Associations work?",
                a: "We use AI to extract key concepts from each guide and find connections across your study history, creating a knowledge graph that grows as you learn.",
              },
            ].map(({ q, a }) => (
              <div key={q} className="border-b border-gray-100 pb-5">
                <h3 className="text-sm font-semibold text-gray-900 mb-1.5">
                  {q}
                </h3>
                <p className="text-sm text-gray-500 leading-relaxed">{a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
