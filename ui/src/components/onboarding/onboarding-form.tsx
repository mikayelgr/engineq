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
          Intelligence-enabled music management system for businesses.
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
