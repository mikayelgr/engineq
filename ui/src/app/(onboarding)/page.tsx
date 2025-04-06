import { check } from "@/src/actions/auth";
import OnboardingForm from "@/src/components/onboarding/onboarding-form";
import { redirect } from "next/navigation";

export default async function Home() {
  const isSignedIn = await check();
  if (isSignedIn) {
    return redirect("/dashboard");
  }

  return (
    <div className="w-full flex items-center justify-center h-screen">
      <OnboardingForm />
    </div>
  );
}
