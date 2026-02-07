import { google } from 'googleapis';
import { JWT } from 'google-auth-library';

// Escopos necessários para Calendar e Drive
const SCOPES = [
  'https://www.googleapis.com/auth/calendar',
  'https://www.googleapis.com/auth/calendar.events',
  'https://www.googleapis.com/auth/drive.readonly'
];

export class GoogleClient {
  private auth: JWT | null = null;
  private calendarId: string;

  constructor() {
    // Tenta carregar credenciais das variáveis de ambiente
    const email = process.env.GOOGLE_CLIENT_EMAIL;
    const key = process.env.GOOGLE_PRIVATE_KEY?.replace(/\\n/g, '\n');
    this.calendarId = process.env.GOOGLE_CALENDAR_ID || 'primary';

    if (email && key) {
      this.auth = new google.auth.JWT({
        email: email,
        key: key,
        scopes: SCOPES
      });
    } else {
        console.warn("️ Google Credentials not found in .env");
    }
  }

  async getCalendarClient() {
    if (!this.auth) return null;
    return google.calendar({ version: 'v3', auth: this.auth });
  }

  async getDriveClient() {
    if (!this.auth) return null;
    return google.drive({ version: 'v3', auth: this.auth });
  }

  async listUpcomingEvents(maxResults = 5) {
    const calendar = await this.getCalendarClient();
    if (!calendar) return [];

    try {
      const res = await calendar.events.list({
        calendarId: this.calendarId,
        timeMin: new Date().toISOString(),
        maxResults: maxResults,
        singleEvents: true,
        orderBy: 'startTime',
      });
      return res.data.items || [];
    } catch (error) {
      console.error("Failed to list events:", error);
      return [];
    }
  }

  async createEvent(summary: string, description: string, startTime: string, endTime: string, attendeeEmail?: string) {
      const calendar = await this.getCalendarClient();
      if (!calendar) return null;

      const event = {
          summary,
          description,
          start: { dateTime: startTime },
          end: { dateTime: endTime },
          attendees: attendeeEmail ? [{ email: attendeeEmail }] : [],
          conferenceData: {
              createRequest: {
                  requestId: Math.random().toString(36).substring(7),
                  conferenceSolutionKey: { type: 'hangoutsMeet' },
              },
          },
      };

      try {
          const res = await calendar.events.insert({
              calendarId: this.calendarId,
              requestBody: event,
              conferenceDataVersion: 1, // Ativa criação do Meet
          });
          return res.data;
      } catch (error) {
          console.error("Failed to create event:", error);
          return null;
      }
  }
  
  async listRecordings(folderId: string) {
      const drive = await this.getDriveClient();
      if (!drive) return [];
      
      try {
          const res = await drive.files.list({
              q: `'${folderId}' in parents and mimeType contains 'video/' and trashed = false`,
              fields: 'files(id, name, createdTime, webViewLink, videoMediaMetadata)',
              orderBy: 'createdTime desc',
              pageSize: 10
          });
          return res.data.files || [];
      } catch (error) {
          console.error("Failed to list recordings:", error);
          return [];
      }
  }
}
