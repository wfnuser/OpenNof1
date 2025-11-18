import { NextResponse } from "next/server";

const blockedResponse = () => {
  const message =
    "Control operations are disabled for security reasons. Set ALLOW_CONTROL_OPERATIONS=true to enable.";

  return NextResponse.json(
    {
      error: "CONTROL_OPERATIONS_DISABLED",
      message,
    },
    { status: 403 }
  );
};

export const GET = blockedResponse;
export const POST = blockedResponse;
export const PUT = blockedResponse;
export const PATCH = blockedResponse;
export const DELETE = blockedResponse;
export const HEAD = blockedResponse;
