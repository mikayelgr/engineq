// EngineQ: An AI-enabled music management system.
// Copyright (C) 2025  Mikayel Grigoryan
// 
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published
// by the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
// 
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
// 
// For inquiries, contact: michael.grigoryan25@gmail.com
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
