var currentPhotoNum = 1;
var maxPhotoNum = 0;
var pageNumber = 1;

function getPhoto(num) {
  return $("photo-" + num);
}

function currentPhoto() {
  return getPhoto(currentPhotoNum);
}

function nextDivNum() {
  for(i = 1; i <= maxPhotoNum; i++) {
    if (getPhoto(i).viewportOffset().top > 0) { break; }
  }
  
  return i;
}

function prevDivNum() {
  nextNum = nextDivNum();
  return (nextNum > 2) ? nextNum - 2 : 1;
}

function nextElement() {
  currentPhotoNum = nextDivNum();
  return currentPhoto();
}

function prevElement() {
  currentPhotoNum = prevDivNum();
  return currentPhoto();
}

Event.observe(window, 'keyup', function(event) {
  switch(event.keyCode) {
    case 74: // "J"
      nextElement().scrollTo();
      currentPhoto().down("a").focus();
      if (maxPhotoNum - currentPhotoNum < 4) { fetchMorePhotos(); }
      break;
    case 75: // "K"
      prevElement().scrollTo(); 
      currentPhoto().down("a").focus();
      break;
  }
});

Ajax.Responders.register({
  onCreate: function() { Ajax.activeRequestCount++; },
  onComplete: function() { Ajax.activeRequestCount--; }
});

document.observe("dom:loaded", function() {
  $("fetch-more").observe("click", function(event) {
    event.stop();
    fetchMorePhotos();
  });
});

function fetchMorePhotos() {
  if (Ajax.activeRequestCount > 0) { return; }
  
  new Ajax.Updater("photos", window.location + "?page=" + (pageNumber + 1), {
    insertion: "bottom",
    method: "get",
    onComplete: function() {
      pageNumber += 1;
      maxPhotoNum += 15;
    }
  });
}