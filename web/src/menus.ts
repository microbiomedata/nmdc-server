// Note: Each object in each `items` array represents a link in a dropdown menu.
//       When defining a link for client-side routing, use the `to` property.
//       When defining a link for server-side routing, use the `href` property.
const Menus = [
  {
    label: 'About Us',
    href: 'https://microbiomedata.org/about/',
    items: [
      {
        label: 'Our Story',
        href: 'https://microbiomedata.org/about/',
      },
      {
        label: 'Team',
        href: 'https://microbiomedata.org/team/',
      },
      {
        label: 'Advisory',
        href: 'https://microbiomedata.org/advisory/',
      },
      {
        label: 'FAQs',
        href: 'https://microbiomedata.org/faqs/',
      },
      {
        label: 'Diversity, Equity, and Inclusion',
        href: 'https://microbiomedata.org/idea-action-plan/',
      },
      {
        label: 'Data Use Policy',
        href: 'https://microbiomedata.org/nmdc-data-use-policy/',
      },
      {
        label: 'Contact Us',
        href: 'https://microbiomedata.org/contact/',
      },
    ],
  },
  {
    label: 'Products',
    items: [
      {
        label: 'Data Portal',
        to: '/',
      },
      {
        label: 'Submission Portal',
        to: '/submission/home',
      },
      {
        label: 'NMDC EDGE',
        href: 'https://nmdc-edge.org',
      },
      {
        label: 'Field Notes Mobile App',
        href: 'https://microbiomedata.org/field-notes/',
      },
    ],
  },
  {
    label: 'Resources',
    items: [
      {
        label: 'Data Standards',
        href: 'https://microbiomedata.org/data-standards/',
      },
      {
        label: 'Bioinformatics Workflows',
        href: 'https://microbiomedata.org/workflows/',
      },
      {
        label: 'GitHub',
        href: 'https://github.com/microbiomedata',
      },
      {
        label: 'Documentation',
        href: 'https://microbiomedata.org/documentation/',
      },
      {
        label: 'Data Management',
        href: 'https://microbiomedata.org/data-management/',
      },
    ],
  },
  {
    label: 'Partner with Us',
    href: 'https://microbiomedata.org/community/',
    items: [
      {
        label: 'Community',
        href: 'https://microbiomedata.org/community/',
      },
      {
        label: 'Ambassadors',
        href: 'https://microbiomedata.org/ambassadors/',
      },
      {
        label: 'Champions',
        href: 'https://microbiomedata.org/community/championsprogram/',
      },
      {
        label: 'User Research',
        href: 'https://microbiomedata.org/user-research/',
      },
    ],
  },
  {
    label: 'News & Impact',
    items: [
      {
        label: 'Annual Reports',
        href: 'https://microbiomedata.org/annual_report/',
      },
      {
        label: 'Blog',
        href: 'https://microbiomedata.org/blog/',
      },
      {
        label: 'Events',
        href: 'https://microbiomedata.org/events/',
      },
      {
        label: 'Media Materials',
        href: 'https://microbiomedata.org/media/',
      },
      {
        label: 'Newsletters',
        href: 'https://microbiomedata.org/newsletters/',
      },
      {
        label: 'Publications',
        href: 'https://microbiomedata.org/publications/',
      },
    ],
  },
];

export default Menus;
