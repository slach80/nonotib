/**
 * College Soccer Coach Outreach CRM
 * For Noah Lach (Class of 2028) recruiting outreach
 *
 * Expected Google Sheet columns:
 * A: School
 * B: Division
 * C: Coach URL
 * D: Roster Window
 * E: Score
 * F: Coach Name
 * G: Coach Email
 * H: Date Contacted
 * I: Response Status
 * J: Notes
 */

// Configuration constants
const CONFIG = {
  FROM_EMAIL: 'noahlach@gmail.com',
  PORTFOLIO_URL: 'https://slach80.github.io/nonotib',
  SPORTSRECRUITS_URL: '[YOUR_SPORTSRECRUITS_PROFILE_URL]', // Update this
  DAILY_EMAIL_LIMIT: 90, // Safety margin under 100/day Gmail limit
  SHEET_NAME: 'Sheet1', // Change if your sheet has a different name
  HEADER_ROW: 1,
  DATA_START_ROW: 2
};

// Column indices (0-based for array access, 1-based for sheet access)
const COLS = {
  SCHOOL: 0,
  DIVISION: 1,
  COACH_URL: 2,
  ROSTER_WINDOW: 3,
  SCORE: 4,
  COACH_NAME: 5,
  COACH_EMAIL: 6,
  DATE_CONTACTED: 7,
  RESPONSE_STATUS: 8,
  NOTES: 9
};

/**
 * Creates custom menu when spreadsheet opens
 */
function onOpen() {
  createEmailMenu();
}

/**
 * Adds custom menu to Google Sheets UI
 */
function createEmailMenu() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Coach Outreach')
    .addItem('Send Email to Selected Row', 'sendEmailToSelectedRow')
    .addItem('Send Bulk Emails (All Uncontacted)', 'sendBulkEmailsWithConfirmation')
    .addSeparator()
    .addItem('Generate Weekly Digest', 'generateWeeklyDigest')
    .addSeparator()
    .addItem('Test Email Template', 'testEmailTemplate')
    .addToUi();
}

/**
 * Sends email to coach in the currently selected row
 */
function sendEmailToSelectedRow() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const activeRange = sheet.getActiveRange();
  const row = activeRange.getRow();

  if (row < CONFIG.DATA_START_ROW) {
    SpreadsheetApp.getUi().alert('Please select a data row (not the header row).');
    return;
  }

  const result = sendCoachEmail(row);

  if (result.success) {
    SpreadsheetApp.getUi().alert(`Email sent successfully to ${result.coachName} at ${result.school}!`);
  } else {
    SpreadsheetApp.getUi().alert(`Error: ${result.error}`);
  }
}

/**
 * Sends personalized email to a specific coach (by row number)
 * @param {number} row - The row number in the sheet (1-based index)
 * @returns {Object} Result object with success status and details
 */
function sendCoachEmail(row) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.SHEET_NAME);
  const data = sheet.getRange(row, 1, 1, 10).getValues()[0];

  const school = data[COLS.SCHOOL];
  const division = data[COLS.DIVISION];
  const coachName = data[COLS.COACH_NAME];
  const coachEmail = data[COLS.COACH_EMAIL];
  const dateContacted = data[COLS.DATE_CONTACTED];

  // Validation
  if (!coachEmail || coachEmail.toString().trim() === '') {
    return { success: false, error: 'No email address found for this coach.' };
  }

  if (dateContacted && dateContacted.toString().trim() !== '') {
    return {
      success: false,
      error: `Coach already contacted on ${Utilities.formatDate(new Date(dateContacted), Session.getScriptTimeZone(), 'MM/dd/yyyy')}`
    };
  }

  if (!school || school.toString().trim() === '') {
    return { success: false, error: 'School name is missing.' };
  }

  // Generate email content
  const emailContent = generateEmailContent(school, division, coachName);

  // Check for unfilled placeholders
  const hasPlaceholders = emailContent.bodyPlain.includes('[') && emailContent.bodyPlain.includes(']');

  try {
    // Send email
    GmailApp.sendEmail(
      coachEmail,
      emailContent.subject,
      emailContent.bodyPlain,
      {
        from: CONFIG.FROM_EMAIL,
        htmlBody: emailContent.bodyHtml,
        name: 'Noah Lach'
      }
    );

    // Mark as contacted
    markAsContacted(row, new Date());

    // Add warning note if placeholders detected
    if (hasPlaceholders) {
      const notesCell = sheet.getRange(row, COLS.NOTES + 1);
      const currentNotes = notesCell.getValue();
      const warningNote = `[${new Date().toLocaleDateString()}] WARNING: Email sent with unfilled placeholders. Review email for [GPA], [Year], [Phone Number], or [specific reason].`;
      notesCell.setValue(currentNotes ? `${currentNotes}\n${warningNote}` : warningNote);
    }

    // Log success
    Logger.log(`Email sent to ${coachName} at ${school} (${coachEmail})`);

    return {
      success: true,
      school: school,
      coachName: coachName,
      coachEmail: coachEmail
    };

  } catch (error) {
    Logger.log(`Error sending email to row ${row}: ${error.toString()}`);

    // Add error note to sheet
    const notesCell = sheet.getRange(row, COLS.NOTES + 1);
    const currentNotes = notesCell.getValue();
    const errorNote = `[${new Date().toLocaleDateString()}] Email send failed: ${error.toString()}`;
    notesCell.setValue(currentNotes ? `${currentNotes}\n${errorNote}` : errorNote);

    return { success: false, error: error.toString() };
  }
}

/**
 * Generates personalized email content for a coach
 * @param {string} school - School name
 * @param {string} division - Division (D1, D2, NAIA, etc.)
 * @param {string} coachName - Coach's name
 * @returns {Object} Email subject and body (plain and HTML)
 */
function generateEmailContent(school, division, coachName) {
  const subject = buildEmailSubject(school);
  const bodyPlain = buildEmailBody(school, coachName, 'plain');
  const bodyHtml = buildEmailBody(school, coachName, 'html');

  return {
    subject: subject,
    bodyPlain: bodyPlain,
    bodyHtml: bodyHtml
  };
}

/**
 * Builds the email subject line
 * @param {string} school - School name
 * @returns {string} Email subject
 */
function buildEmailSubject(school) {
  return `Class of 2028 Midfielder - Noah Lach - ${school}`;
}

/**
 * Builds the email body (plain text or HTML)
 * @param {string} school - School name
 * @param {string} coachName - Coach's name
 * @param {string} format - 'plain' or 'html'
 * @returns {string} Email body
 */
function buildEmailBody(school, coachName, format) {
  // Extract coach's last name
  const greeting = coachName && coachName.toString().trim() !== ''
    ? `Dear Coach ${coachName.split(' ').pop()},`
    : 'Dear Coach,';

  // Define placeholders (to be manually filled)
  const placeholders = {
    specificReason: '[specific reason - will be filled manually or left as placeholder]',
    achievement: 'competed at the MLS Next level with Sporting KC Academy',
    gpa: '[GPA]',
    satYear: '[Year]',
    phoneNumber: '[Phone Number - leave blank for manual entry]'
  };

  if (format === 'html') {
    return `
    <p>${greeting}</p>

    <p>My name is Noah Lach, and I am a Class of 2028 center midfielder/forward from Sporting Kansas City Academy in Kansas City, Missouri.</p>

    <p>I am very interested in your program at ${school} because ${placeholders.specificReason}.</p>

    <p>Here is my recruiting portfolio: <a href="${CONFIG.PORTFOLIO_URL}">${CONFIG.PORTFOLIO_URL}</a><br>
    Here is my SportsRecruits profile: <a href="${CONFIG.SPORTSRECRUITS_URL}">${CONFIG.SPORTSRECRUITS_URL}</a></p>

    <p>This past season, I ${placeholders.achievement}.</p>

    <p>My current GPA is ${placeholders.gpa} and I am preparing for SAT testing in ${placeholders.satYear}.</p>

    <p>I would really appreciate any feedback on where I stand with your program and what I should focus on improving.</p>

    <p>Thank you for your time, and I hope to speak with you soon.</p>

    <p>Best regards,<br>
    Noah Lach<br>
    Midfielder/Forward | Class of 2028<br>
    Sporting Kansas City Academy<br>
    ${placeholders.phoneNumber}<br>
    <a href="mailto:${CONFIG.FROM_EMAIL}">${CONFIG.FROM_EMAIL}</a><br>
    Portfolio: <a href="${CONFIG.PORTFOLIO_URL}">${CONFIG.PORTFOLIO_URL}</a></p>
  `;
  } else {
    // Plain text format
    return `${greeting}

My name is Noah Lach, and I am a Class of 2028 center midfielder/forward from Sporting Kansas City Academy in Kansas City, Missouri.

I am very interested in your program at ${school} because ${placeholders.specificReason}.

Here is my recruiting portfolio: ${CONFIG.PORTFOLIO_URL}
Here is my SportsRecruits profile: ${CONFIG.SPORTSRECRUITS_URL}

This past season, I ${placeholders.achievement}.

My current GPA is ${placeholders.gpa} and I am preparing for SAT testing in ${placeholders.satYear}.

I would really appreciate any feedback on where I stand with your program and what I should focus on improving.

Thank you for your time, and I hope to speak with you soon.

Best regards,
Noah Lach
Midfielder/Forward | Class of 2028
Sporting Kansas City Academy
${placeholders.phoneNumber}
${CONFIG.FROM_EMAIL}
Portfolio: ${CONFIG.PORTFOLIO_URL}`;
  }
}

/**
 * Marks a row as contacted with timestamp
 * @param {number} row - Row number (1-based)
 * @param {Date} timestamp - Date/time of contact
 */
function markAsContacted(row, timestamp) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.SHEET_NAME);

  // Update Date Contacted column
  sheet.getRange(row, COLS.DATE_CONTACTED + 1).setValue(timestamp);

  // Set Response Status to "Awaiting Response"
  sheet.getRange(row, COLS.RESPONSE_STATUS + 1).setValue('Awaiting Response');
}

/**
 * Shows confirmation dialog before sending bulk emails
 */
function sendBulkEmailsWithConfirmation() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.SHEET_NAME);
  const lastRow = sheet.getLastRow();

  // Count uncontacted coaches
  let uncontactedCount = 0;
  for (let i = CONFIG.DATA_START_ROW; i <= lastRow; i++) {
    const dateContacted = sheet.getRange(i, COLS.DATE_CONTACTED + 1).getValue();
    const email = sheet.getRange(i, COLS.COACH_EMAIL + 1).getValue();

    if (email && email.toString().trim() !== '' &&
        (!dateContacted || dateContacted.toString().trim() === '')) {
      uncontactedCount++;
    }
  }

  if (uncontactedCount === 0) {
    SpreadsheetApp.getUi().alert('No uncontacted coaches found. All coaches with email addresses have been contacted.');
    return;
  }

  // Check against daily limit
  if (uncontactedCount > CONFIG.DAILY_EMAIL_LIMIT) {
    SpreadsheetApp.getUi().alert(
      `Warning: You have ${uncontactedCount} uncontacted coaches, but the daily limit is ${CONFIG.DAILY_EMAIL_LIMIT}. ` +
      `Only the first ${CONFIG.DAILY_EMAIL_LIMIT} will be sent. Run this again tomorrow for the rest.`
    );
  }

  const ui = SpreadsheetApp.getUi();
  const response = ui.alert(
    'Confirm Bulk Email Send',
    `This will send emails to ${Math.min(uncontactedCount, CONFIG.DAILY_EMAIL_LIMIT)} uncontacted coaches. Continue?`,
    ui.ButtonSet.YES_NO
  );

  if (response === ui.Button.YES) {
    sendBulkEmails();
  }
}

/**
 * Sends emails to all coaches where "Date Contacted" is empty
 * Respects daily email limits and provides progress updates
 * @returns {Object} Summary of results
 */
function sendBulkEmails() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.SHEET_NAME);
  const lastRow = sheet.getLastRow();

  let sentCount = 0;
  let errorCount = 0;
  const errors = [];

  for (let i = CONFIG.DATA_START_ROW; i <= lastRow; i++) {
    // Check daily limit
    if (sentCount >= CONFIG.DAILY_EMAIL_LIMIT) {
      Logger.log(`Reached daily email limit of ${CONFIG.DAILY_EMAIL_LIMIT}. Stopping.`);
      break;
    }

    const dateContacted = sheet.getRange(i, COLS.DATE_CONTACTED + 1).getValue();
    const email = sheet.getRange(i, COLS.COACH_EMAIL + 1).getValue();
    const school = sheet.getRange(i, COLS.SCHOOL + 1).getValue();

    // Skip if already contacted or no email
    if (!email || email.toString().trim() === '') {
      continue;
    }

    if (dateContacted && dateContacted.toString().trim() !== '') {
      continue;
    }

    // Send email
    const result = sendCoachEmail(i);

    if (result.success) {
      sentCount++;
      Logger.log(`[${sentCount}] Sent to ${school}`);

      // Add small delay to avoid rate limiting (0.5 seconds between emails)
      Utilities.sleep(500);
    } else {
      errorCount++;
      errors.push(`Row ${i} (${school}): ${result.error}`);
      Logger.log(`Error on row ${i}: ${result.error}`);
    }
  }

  // Show summary
  let message = `Bulk email send complete!\n\n`;
  message += `Successfully sent: ${sentCount}\n`;
  message += `Errors: ${errorCount}\n`;

  if (errorCount > 0) {
    message += `\nErrors:\n${errors.join('\n')}`;
  }

  SpreadsheetApp.getUi().alert(message);

  return {
    sent: sentCount,
    errors: errorCount,
    errorDetails: errors
  };
}

/**
 * Generates a weekly digest of outreach activity
 * Creates a summary document or sends an email
 */
function generateWeeklyDigest() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.SHEET_NAME);
  const lastRow = sheet.getLastRow();
  const data = sheet.getRange(CONFIG.DATA_START_ROW, 1, lastRow - CONFIG.HEADER_ROW, 10).getValues();

  const now = new Date();
  const oneWeekAgo = new Date(now.getTime() - (7 * 24 * 60 * 60 * 1000));

  let totalContacted = 0;
  let contactedThisWeek = 0;
  let responsesReceived = 0;
  let awaitingResponse = 0;
  let followUpsNeeded = [];
  let recentContacts = [];

  data.forEach((row, index) => {
    const school = row[COLS.SCHOOL];
    const coachName = row[COLS.COACH_NAME];
    const dateContacted = row[COLS.DATE_CONTACTED];
    const responseStatus = row[COLS.RESPONSE_STATUS];

    if (dateContacted && dateContacted.toString().trim() !== '') {
      totalContacted++;

      const contactDate = new Date(dateContacted);

      // Count contacts this week
      if (contactDate >= oneWeekAgo) {
        contactedThisWeek++;
        recentContacts.push({ school, coachName, date: contactDate });
      }

      // Count responses
      if (responseStatus && responseStatus.toString().toLowerCase().includes('response')) {
        if (responseStatus.toString().toLowerCase().includes('awaiting')) {
          awaitingResponse++;

          // Check if follow-up needed (more than 2 weeks old)
          const twoWeeksAgo = new Date(now.getTime() - (14 * 24 * 60 * 60 * 1000));
          if (contactDate < twoWeeksAgo) {
            followUpsNeeded.push({
              school,
              coachName,
              date: contactDate,
              daysWaiting: Math.floor((now - contactDate) / (24 * 60 * 60 * 1000))
            });
          }
        } else if (responseStatus.toString().toLowerCase().includes('received')) {
          responsesReceived++;
        }
      }
    }
  });

  const uncontacted = data.length - totalContacted;
  const responseRate = totalContacted > 0 ? ((responsesReceived / totalContacted) * 100).toFixed(1) : 0;

  // Generate digest
  let digest = `NOAH LACH RECRUITING OUTREACH - WEEKLY DIGEST\n`;
  digest += `Generated: ${now.toLocaleDateString()} ${now.toLocaleTimeString()}\n`;
  digest += `${'='.repeat(60)}\n\n`;

  digest += `OVERVIEW\n`;
  digest += `${'—'.repeat(60)}\n`;
  digest += `Total Schools in Database: ${data.length}\n`;
  digest += `Total Contacted: ${totalContacted}\n`;
  digest += `Contacted This Week: ${contactedThisWeek}\n`;
  digest += `Responses Received: ${responsesReceived}\n`;
  digest += `Awaiting Response: ${awaitingResponse}\n`;
  digest += `Uncontacted: ${uncontacted}\n`;
  digest += `Response Rate: ${responseRate}%\n\n`;

  if (recentContacts.length > 0) {
    digest += `COACHES CONTACTED THIS WEEK\n`;
    digest += `${'—'.repeat(60)}\n`;
    recentContacts.forEach(contact => {
      digest += `- ${contact.school}`;
      if (contact.coachName) digest += ` (${contact.coachName})`;
      digest += ` - ${contact.date.toLocaleDateString()}\n`;
    });
    digest += `\n`;
  }

  if (followUpsNeeded.length > 0) {
    digest += `FOLLOW-UPS NEEDED (2+ weeks, no response)\n`;
    digest += `${'—'.repeat(60)}\n`;
    followUpsNeeded.forEach(followUp => {
      digest += `- ${followUp.school}`;
      if (followUp.coachName) digest += ` (${followUp.coachName})`;
      digest += ` - ${followUp.daysWaiting} days waiting\n`;
    });
    digest += `\n`;
  }

  digest += `NEXT STEPS\n`;
  digest += `${'—'.repeat(60)}\n`;
  if (uncontacted > 0) {
    digest += `- Reach out to ${Math.min(uncontacted, CONFIG.DAILY_EMAIL_LIMIT)} remaining uncontacted schools\n`;
  }
  if (followUpsNeeded.length > 0) {
    digest += `- Send follow-up emails to ${followUpsNeeded.length} non-responders\n`;
  }
  if (awaitingResponse > 0) {
    digest += `- Monitor ${awaitingResponse} coaches for responses\n`;
  }
  digest += `- Update Response Status column as replies come in\n`;
  digest += `- Add new schools to target list if needed\n\n`;

  digest += `${'='.repeat(60)}\n`;
  digest += `Keep up the great work!\n`;

  // Log digest
  Logger.log(digest);

  // Show in dialog
  const ui = SpreadsheetApp.getUi();
  const response = ui.alert(
    'Weekly Digest Generated',
    'The digest has been generated. Would you like to:\n\n1. View it now (select YES)\n2. Email it to yourself (select NO)\n3. Cancel (select CANCEL)',
    ui.ButtonSet.YES_NO_CANCEL
  );

  if (response === ui.Button.YES) {
    // Show in a text dialog (truncated if too long)
    const maxLength = 1000;
    const displayDigest = digest.length > maxLength
      ? digest.substring(0, maxLength) + '\n\n[Truncated - check logs for full digest]'
      : digest;
    ui.alert('Weekly Digest', displayDigest, ui.ButtonSet.OK);
  } else if (response === ui.Button.NO) {
    // Email digest
    GmailApp.sendEmail(
      CONFIG.FROM_EMAIL,
      `Noah Lach Recruiting - Weekly Digest ${now.toLocaleDateString()}`,
      digest
    );
    ui.alert('Weekly digest emailed to ' + CONFIG.FROM_EMAIL);
  }

  return digest;
}

/**
 * Sends a test email to verify template and configuration
 */
function testEmailTemplate() {
  const ui = SpreadsheetApp.getUi();
  const response = ui.alert(
    'Test Email',
    `This will send a test email to ${CONFIG.FROM_EMAIL} using the template. Continue?`,
    ui.ButtonSet.YES_NO
  );

  if (response !== ui.Button.YES) {
    return;
  }

  const emailContent = generateEmailContent(
    'Sample University',
    'D1',
    'John Smith'
  );

  try {
    GmailApp.sendEmail(
      CONFIG.FROM_EMAIL,
      '[TEST] ' + emailContent.subject,
      emailContent.bodyPlain,
      {
        htmlBody: emailContent.bodyHtml,
        name: 'Noah Lach'
      }
    );

    ui.alert('Test email sent successfully to ' + CONFIG.FROM_EMAIL);
  } catch (error) {
    ui.alert('Error sending test email: ' + error.toString());
  }
}

/**
 * Utility: Returns count of emails sent today (approximate)
 * Note: This uses the Sent folder which may not be 100% accurate
 * @returns {number} Approximate count of emails sent today
 */
function getEmailsSentToday() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const threads = GmailApp.search(`from:${CONFIG.FROM_EMAIL} after:${Utilities.formatDate(today, Session.getScriptTimeZone(), 'yyyy/MM/dd')}`);

  let count = 0;
  threads.forEach(thread => {
    count += thread.getMessageCount();
  });

  return count;
}
