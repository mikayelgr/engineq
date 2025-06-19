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

import { useEffect } from "react";
import { Button, Card, CardBody, CardHeader } from "@heroui/react";
import { AlertTriangle } from "lucide-react";

export default function Error({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex h-full w-full items-center justify-center p-4">
      <Card className="max-w-md w-full shadow-lg p-6 flex flex-col text-center">
        <div className="flex flex-col text-red-500 mb-4">
          <AlertTriangle size={50} />
        </div>
        <CardHeader className="p-0">
          <h2 className="text-2xl font-semibold text-center">
            Something went wrong!
          </h2>
        </CardHeader>
        <CardBody className="p-0 mt-2">
          <p className="text-gray-600 mb-6">
            An unexpected error occurred. Please try again.
          </p>
          <Button
            onPress={reset}
            color="primary"
            className="w-full py-2 text-lg"
          >
            Try Again
          </Button>
        </CardBody>
      </Card>
    </div>
  );
}
