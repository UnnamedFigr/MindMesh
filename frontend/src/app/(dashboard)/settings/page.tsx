"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useCredits } from "@/hooks/useCredits";
import { formatTimeUntilReset } from "@/lib/utils";
import Button from "@/components/ui/Button";
import Card, { CardHeader, CardBody } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import {
  Settings,
  User,
  CreditCard,
  Target,
  Crown,
  Mail,
  Clock,
  Shield,
  ExternalLink,
} from "lucide-react";

export default function SettingsPage() {
  const { user, signOut } = useAuth();
  const { credits, loading: creditsLoading, refresh } = useCredits();
  const [signingOut, setSigningOut] = useState(false);

  const handleSignOut = async () => {
    setSigningOut(true);
    await signOut();
  };

  const tier = credits?.tier ?? "free";
  const isPro = tier === "pro";

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center">
          <Settings className="w-5 h-5 text-indigo-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-sm text-gray-500">
            Manage your account and subscription
          </p>
        </div>
      </div>

      <div className="space-y-6">
        {/* Profile */}
        <Card>
          <CardHeader>
            <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
              <User className="w-4 h-4 text-gray-500" />
              Profile
            </h2>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
                    <span className="text-indigo-600 font-semibold text-sm">
                      {user?.email?.charAt(0).toUpperCase() ?? "?"}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {user?.user_metadata?.full_name || user?.email || "User"}
                    </p>
                    <p className="text-xs text-gray-500 flex items-center gap-1">
                      <Mail className="w-3 h-3" />
                      {user?.email}
                    </p>
                  </div>
                </div>
                <Badge variant={isPro ? "success" : "default"}>
                  {isPro ? (
                    <>
                      <Crown className="w-3 h-3 mr-1" />
                      Pro
                    </>
                  ) : (
                    "Free"
                  )}
                </Badge>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Credits & Subscription */}
        <Card>
          <CardHeader>
            <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
              <Target className="w-4 h-4 text-gray-500" />
              Credits & Usage
            </h2>
          </CardHeader>
          <CardBody>
            {creditsLoading || !credits ? (
              <div className="animate-pulse space-y-3">
                <div className="h-4 bg-gray-200 rounded w-1/2" />
                <div className="h-3 bg-gray-200 rounded w-1/3" />
              </div>
            ) : (
              <div className="space-y-4">
                {/* Usage Bar */}
                <div>
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-gray-600">Daily Credits</span>
                    <span className="font-medium text-gray-900">
                      {credits.credits_remaining} / {credits.daily_credit_limit}{" "}
                      remaining
                    </span>
                  </div>
                  <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        credits.credits_remaining <= 1
                          ? "bg-red-500"
                          : credits.credits_remaining <=
                            credits.daily_credit_limit / 2
                          ? "bg-yellow-500"
                          : "bg-indigo-500"
                      }`}
                      style={{
                        width: `${
                          (credits.credits_remaining /
                            credits.daily_credit_limit) *
                          100
                        }%`,
                      }}
                    />
                  </div>
                  {credits.reset_at && (
                    <p className="text-xs text-gray-400 mt-1.5 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Resets in {formatTimeUntilReset(credits.reset_at)}
                    </p>
                  )}
                </div>

                {/* Tier Comparison */}
                <div className="bg-gray-50 rounded-xl p-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div
                      className={`p-3 rounded-lg border-2 ${
                        !isPro
                          ? "border-indigo-500 bg-white"
                          : "border-gray-200 bg-white"
                      }`}
                    >
                      <p className="text-xs font-medium text-gray-500 mb-1">
                        Free Tier
                      </p>
                      <p className="text-lg font-bold text-gray-900">
                        3 credits/day
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        Basic study guides
                      </p>
                    </div>
                    <div
                      className={`p-3 rounded-lg border-2 ${
                        isPro
                          ? "border-indigo-500 bg-white"
                          : "border-gray-200 bg-white"
                      }`}
                    >
                      <p className="text-xs font-medium text-indigo-600 mb-1 flex items-center gap-1">
                        <Crown className="w-3 h-3" />
                        Pro Tier
                      </p>
                      <p className="text-lg font-bold text-gray-900">
                        15 credits/day
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        + Quiz, Reflections, Associations
                      </p>
                    </div>
                  </div>
                </div>

                {!isPro && (
                  <Button className="w-full" size="lg">
                    <Crown className="w-4 h-4 mr-2" />
                    Upgrade to Pro — $9.99/mo
                  </Button>
                )}
              </div>
            )}
          </CardBody>
        </Card>

        {/* Security */}
        <Card>
          <CardHeader>
            <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
              <Shield className="w-4 h-4 text-gray-500" />
              Account
            </h2>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    Sign out
                  </p>
                  <p className="text-xs text-gray-500">
                    Log out of your MindMesh account
                  </p>
                </div>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={handleSignOut}
                  loading={signingOut}
                >
                  Sign Out
                </Button>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
