import { NextRequest, NextResponse } from "next/server";

export async function middleware(request: NextRequest): Promise<NextResponse> {
  // On-site request validation
  if (request.nextUrl.pathname.startsWith("/api")) {
    const hostHeader = request.headers.get("host");
    const expectedHost = new URL(request.url).host;

    if (!hostHeader || hostHeader !== expectedHost) {
      return NextResponse.json(
        { error: "Forbidden: External requests blocked" },
        { status: 403 }
      );
    }
  }

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
