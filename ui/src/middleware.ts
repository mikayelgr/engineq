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

import { NextRequest, NextResponse } from "next/server";

export async function middleware(request: NextRequest): Promise<NextResponse> {
  // Authentication
  const c = request.cookies.get("lck");
  if (!c || c.value.length === 0) {
    // In case of API routes, make sure that we can only send the request if authenticated
    if (request.nextUrl.pathname.includes("/api")) {
      return NextResponse.json({ error: "Forbidden" }, { status: 403 });
    }

    // This is the required way for constructing response URLs in middleware
    return NextResponse.redirect(new URL("/", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/api/:path*"],
};
