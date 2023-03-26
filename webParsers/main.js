function getImg(){
    return document.getElementsByClassName('card-image')[0].getElementsByTagName('img')[0].src;
}

function downloadImg(base64str, filename){
    a = document.createElement("a");
    a.href = base64str;
    a.download = filename;
    a.click();
}

function getStars(){
    text = document.getElementsByClassName('stars')[0].parentElement.getElementsByTagName('span')[0].textContent;
    stars = text.replace(')', '').replace('(', '').split(' ');
    return [stars[0], stars[1]];
}

function getCountry(){
    return document.getElementsByClassName('more_title')[0].textContent;
}

function getRandRate(min, max){
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

function getRateElemPos(rate){
    rect = document.getElementsByClassName('ng5-slider-span ng5-slider-bar')[0].getBoundingClientRect();
    xPos = rect.x + (rect.width * 0.1) * rate;
    yPos = rect.y + (rect.height * 0.5);
    return [xPos, yPos];
}

function getRandomId(){
    return Math.random().toString(16).slice(2);
}

function sendRate(rate){
    pos = getRateElemPos(rate);
    xPos = pos[0];
    yPos = pos[1];
    mDown = new MouseEvent('mousedown', {bubbles: true, cancelable: true, composed: true, button: 0, buttons: 1, clientX: xPos, clientY: yPos});
    mUp = new MouseEvent('mouseup', {bubbles: true, cancelable: true, composed: true, button: 0, buttons: 1, clientX: xPos, clientY: yPos});
    document.querySelectorAll('span.ng5-slider-span.ng5-slider-bar-wrapper.ng5-slider-full-bar')[0].dispatchEvent(mDown);
    document.querySelectorAll('span.ng5-slider-span.ng5-slider-bar-wrapper.ng5-slider-full-bar')[0].dispatchEvent(mUp);
}

function removeBanners(){
    banners = document.getElementsByClassName("cdk-overlay-pane");
    overlays = document.getElementsByClassName('cdk-overlay-backdrop cdk-overlay-dark-backdrop cdk-overlay-backdrop-showing');
    for (item of banners){
        item.remove();
    }
    for (item of overlays){
        item.remove();
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }


async function main(stop, gender, format, minRate, maxRate, pause){
    for (let i = 0; i < stop; i++){
        isFirst = false;
        b64img = getImg();
        country = getCountry();
        rate = getRandRate(minRate, maxRate);
        randId = getRandomId();
        sendRate(rate);
        removeBanners();
        await sleep(pause);
        removeBanners();
        stars = getStars();
        downloadImg(b64img, randId + '_' + gender + '_' + country + '_' + stars[0] + '_' + stars[1] + '.' + format);
    }
}

// await main(500, 'm', 'png', 4, 6, 4000)