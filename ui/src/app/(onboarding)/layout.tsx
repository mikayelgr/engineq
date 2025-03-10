import { check } from "@/src/actions/auth";
import { redirect } from "next/navigation";

export default async function Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  const isSignedIn = await check();
  if (!isSignedIn) return redirect("/dashboard");
  return children;
}
