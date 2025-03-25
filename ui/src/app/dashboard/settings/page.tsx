import SettingsForm from "@/src/components/settings/form";

export default async function Settings() {
  return (
    <div className="w-full h-full flex gap-4 flex-col">
      <div className="w-full text-4xl font-bold">Settings</div>
      <SettingsForm />
    </div>
  );
}
