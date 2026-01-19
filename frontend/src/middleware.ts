import { NextRequest, NextResponse } from 'next/server'

const ALWAYS_BLOCKED_PATHS = ['/api/agent/analyze']

const CONTROLLED_PATHS = [
  '/api/agent/start',
  '/api/agent/stop',
  '/api/trading/history/reset',
  '/api/trading/history/sync',
]

const WRITE_ONLY_BLOCKED_PATHS = ['/api/trading/strategy']
const WRITE_BLOCKED_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])

function normalizePath(pathname: string) {
  if (pathname === '/') return pathname
  return pathname.endsWith('/') ? pathname.slice(0, -1) : pathname
}

function rewriteToBlocked(request: NextRequest) {
  const blockedUrl = request.nextUrl.clone()
  blockedUrl.pathname = '/api/frontend-blocked'
  return NextResponse.rewrite(blockedUrl)
}

export function middleware(request: NextRequest) {
  const pathname = normalizePath(request.nextUrl.pathname)

  if (ALWAYS_BLOCKED_PATHS.includes(pathname)) {
    return rewriteToBlocked(request)
  }

  const envControlDisabled = process.env.ALLOW_CONTROL_OPERATIONS === 'false'

  if (envControlDisabled) {
    if (CONTROLLED_PATHS.includes(pathname)) {
      return rewriteToBlocked(request)
    }

    if (
      WRITE_ONLY_BLOCKED_PATHS.includes(pathname) &&
      WRITE_BLOCKED_METHODS.has(request.method)
    ) {
      return rewriteToBlocked(request)
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/api/:path*'],
}
