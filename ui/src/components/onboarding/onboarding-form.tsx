"use client";

import { signin } from "@/src/actions/auth";
import { title } from "@/src/components/primitives";
import { Form, Input, Button } from "@heroui/react";

export default function OnboardingForm() {
  return (
    <div className="max-w-md w-full flex flex-col gap-6">
      <div className="flex flex-col w-full gap-2">
        <h1 className={title({ size: "sm" })}>EngineQ</h1>
        <p className={"text-gray-400 text-sm"}>
          Intelligence-enabled music management system for your business.
        </p>
      </div>

      <Form action={signin} className="w-full">
        <Input
          isRequired
          label="License Key"
          labelPlacement="inside"
          name="key"
          placeholder="engineq-20XX-XXXXXX"
          type="text"
        />

        <Button fullWidth type="submit" variant="bordered">
          Start EngineQ
        </Button>
      </Form>
    </div>
  );
}
