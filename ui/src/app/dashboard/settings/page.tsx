"use client";

import { getPrompts } from "@/src/actions/sub";
import { Spinner, Textarea } from "@heroui/react";
import { useEffect, useState } from "react";

export default function Settings() {
  const [prompt, setPrompt] = useState<string>("");
  const [isFetching, setIsFetching] = useState(true);

  useEffect(() => {
    getPrompts().then((res) => {
      setPrompt(res.prompt);
      setIsFetching(false);
    });
  }, []);

  return (
    <div className="w-full h-full flex gap-4 flex-col">
      <div className="w-full text-4xl font-bold">Settings</div>

      <div>
        {isFetching ? (
          <Spinner variant="spinner" />
        ) : (
          <Textarea
            label="User Prompt for AI Processing"
            color="primary"
            variant="faded"
            isRequired
            name="prompt"
            autoCorrect="off"
            defaultValue={prompt}
            onChange={(e) => setPrompt(e.currentTarget.value)}
          />
        )}
      </div>
    </div>
  );
}
