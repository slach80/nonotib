# TODO

## Security / Access Control
- `index.html` = public; all other pages need protection
- Key decisions still open:
  - Hosting: GitHub Pages vs. Netlify (Netlify recommended for server-side auth)
  - Access model: single shared password vs. per-person links/tokens
  - Audience: family only, or coaches too? Same access level or different?
- Leading option: Netlify host-level password protection (free, true server-side, no code changes)

## colleges.html — Coach Contacts
Research and add direct coach emails/phones for schools that currently only have generic athletics site links:
- **KC/MO:** Evangel, Missouri Western, William Jewell, UMKC, Southwest Baptist, Truman State, Missouri State
- **Tampa Bay:** Southeastern, Saint Leo, Warner, University of Tampa, Eckerd, Lynn, USF
- **California:** San Diego Christian, SJSU, Cal State East Bay, SDSU, USD

## Family Website (future project)
- Two boys: Noah and Isaac — each with a public profile + private personal pages
- Shared pages TBD
- Hosting: AWS (future), custom domain pending; Netlify as interim bridge
- Structure: `noah.domain.com` / `isaac.domain.com` — roll nonotib content into Noah's section
- **Noah pages:** profile (public), college analysis, college map, scholarships, camps, test prep
- **Isaac pages:** profile (public), piano/music, college map (same recruiting concept as Noah), test prep, more TBD
- Security model ties into access control item above
- Design/structure — plan before building
