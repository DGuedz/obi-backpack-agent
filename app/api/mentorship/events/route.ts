import { NextResponse } from 'next/server';
import { GoogleClient } from '@/app/lib/google';

export const dynamic = 'force-dynamic';

export async function GET() {
  const googleClient = new GoogleClient();
  
  const missingEnv: string[] = [];
  if (!process.env.GOOGLE_CLIENT_EMAIL) missingEnv.push("GOOGLE_CLIENT_EMAIL");
  if (!process.env.GOOGLE_PRIVATE_KEY) missingEnv.push("GOOGLE_PRIVATE_KEY");

  if (missingEnv.length > 0) {
      return NextResponse.json({
          connected: false,
          missingEnv,
          events: [
              { id: 'mock1', summary: 'Weekly Market Sync (Mock)', start: { dateTime: new Date().toISOString() }, description: 'Community Call' },
              { id: 'mock2', summary: 'Risk Management Class (Mock)', start: { dateTime: new Date(Date.now() + 86400000).toISOString() }, description: 'Masterclass' }
          ]
      });
  }

  try {
      const events = await googleClient.listUpcomingEvents(5);
      return NextResponse.json({
          connected: true,
          events: events
      });
  } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Unexpected error';
      return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function POST(req: Request) {
    try {
        const { title, date, email } = await req.json();
        
        const googleClient = new GoogleClient();
        const missingEnv: string[] = [];
        if (!process.env.GOOGLE_CLIENT_EMAIL) missingEnv.push("GOOGLE_CLIENT_EMAIL");
        if (!process.env.GOOGLE_PRIVATE_KEY) missingEnv.push("GOOGLE_PRIVATE_KEY");
        if (missingEnv.length > 0) {
            return NextResponse.json({ success: true, mock: true, missingEnv, message: "Mock Event Created" });
        }

        // Criar evento de 1h
        const startTime = new Date(date);
        const endTime = new Date(startTime.getTime() + 3600000); // +1h

        const event = await googleClient.createEvent(
            title || "Mentoria Solo OBIWORK",
            "Sessão individual com Engenheiro OBI.",
            startTime.toISOString(),
            endTime.toISOString(),
            email
        );

        return NextResponse.json({ success: true, event });

    } catch (error: unknown) {
        const message = error instanceof Error ? error.message : 'Unexpected error';
        return NextResponse.json({ error: message }, { status: 500 });
    }
}
