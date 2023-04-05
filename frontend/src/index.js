import React, { useRef } from 'react';
import ReactDOM from 'react-dom/client';
import '../node_modules/bootstrap/dist/css/bootstrap.min.css';
import './index.css';


const host = 'http://127.0.0.1:80';


function ImagesGallery({images, showRates, rates}) {
  return (
    <div className="d-flex flex-wrap justify-content-center" id="gallery">
      {
        images.map((img, index) => {
          return (
            <div className="card bg-white d-inline-flex flex-column justify-content-between" key={index}>
              <div className="img-wrapper flex-grow-1">
                <img src={img} alt="" />
              </div>
              <div className={"rate-wrapper d-flex justify-content-center" + (showRates ? "" : " d-none")}>
                <div className="progress h-100">
                  <span className="h4">{rates[index].toString()}</span>
                  <div
                    className="progress-bar"
                    role="progressbar"
                    aria-valuenow={rates[index].toString()}
                    aria-valuemin="0"
                    aria-valuemax="10"
                    style={{width: (rates[index] * 10).toString() + "%"}}
                  ></div>
                </div>
              </div>
            </div>
          );
        })
      }
    </div>
  );
}


function ImagesControlButtons({
  handleMultipleImages,
  handleClearImages,
  handleSendImages,
  images,
  imagesIsChanged,
  gender,
}) {
  const ref = useRef(null);
  const handleUpload = (e) => {
    ref.current.value = "";
    ref.current.click();
  }
  return (
    <div className="d-inline-flex justify-content-center w-100" id="upload_btns">
      <div className="p-3">
        <button
          type="button"
          className="btn btn-outline-primary btn-lg h-100"
          onClick={() => handleUpload()}
        >
          <span className="h1">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="32"
              height="32"
              fill="currentColor"
              className="bi bi-plus-lg"
              viewBox="0 0 16 16"
            >
              <path
                fillRule="evenodd"
                d="M8 2a.5.5 0 0 1 .5.5v5h5a.5.5 0 0 1 0 1h-5v5a.5.5 0 0 1-1 0v-5h-5a.5.5 0 0 1 0-1h5v-5A.5.5 0 0 1 8 2Z"
              />
            </svg>
          </span>
        </button>
      </div>
      <div className="p-3">
        <button
          type="button"
          className="btn btn-outline-success btn-lg h-100"
          onClick={() => handleSendImages()}
          disabled={images.length === 0 || !imagesIsChanged || !gender}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="32"
            height="32"
            fill="currentColor"
            className="bi bi-check2"
            viewBox="0 0 16 16"
          >
            <path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/>
          </svg>
        </button>
      </div>
      <div className="p-3">
        <button
          type="button"
          className="btn btn-outline-danger btn-lg h-100"
          onClick={() => handleClearImages()}
          disabled={images.length === 0}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="32"
            height="32"
            fill="currentColor"
            className="bi bi-x-lg"
            viewBox="0 0 16 16"
          >
            <path d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"/>
          </svg>
        </button>
      </div>
      <input
          id="image_uploads"
          type="file"
          ref={ref}
          onChange={(e) => handleMultipleImages(e)}
          accept="image/*"
          multiple
        />
    </div>
  );
}


function toBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = error => reject(error);
  });
}


function getRates(imgs, gender) {
  return Promise.all(
    Array.from(imgs).map(img => {
      return toBase64(img)
      .then(b64 => b64.split(',').at(-1));
    })
  ).then(instances => fetch(
      host + ((gender === "m") ? "/man/predict" : "/woman/predict"),
      {
        method: "POST",
        body: JSON.stringify({"instances": instances}),
        headers: {
          "Content-Type": "application/json",
        },
      }
    )
  ).then((r) => {
    if (r.ok) {
      return r.json();
    } else {
      let message = "status: " + r.status;
      if (r.status === 413) {
        message = "Файлы слишком большие. Попробуйте уменьшить их количество или размер";
      }
      alert(message);
      throw new Error(message);
    }
  });
}


class PreviewMultipleImages extends React.Component {
  constructor(props) {
    super(props);
    this.handleMultipleImages = this.handleMultipleImages.bind(this);
    this.handleClearImages = this.handleClearImages.bind(this);
    this.handleSendImages = this.handleSendImages.bind(this);
    this.handleGenderToombler = this.handleGenderToombler.bind(this);
    this.state = {
      images: [],
      showRates: false,
      imagesIsChanged: true,
      rates: [],
      gender: "",
      imagesBlobs: [],
    }
  }

  handleGenderToombler(e) {
    this.setState({
      gender: (e.target.id === "mCheckBox") ? "m" : "w",
    })
  }

  handleMultipleImages(e) {
    if (e.target.files.length > 4) {
      alert("Максимальное количество файлов - 4");
      return;
    };
    const selectedFIles =[];
    const targetFiles = e.target.files;
    const targetFilesObject = [...targetFiles];
    targetFilesObject.map((file) => {
      return selectedFIles.push(URL.createObjectURL(file));
    })
    this.setState({
      images: selectedFIles,
      showRates: false,
      imagesIsChanged: true,
      rates: Array(selectedFIles.length).fill(0.0),
      imagesBlobs: e.target.files,
    });
  }

  handleClearImages() {
    this.setState({
      images: [],
      showRates: false,
      imagesIsChanged: true,
    });
  }

  handleSendImages() {
    this.setState({
      imagesIsChanged: false,
    })
    getRates(this.state.imagesBlobs, this.state.gender)
    .then(predictions => {
      this.setState({
        showRates: true,
        rates: predictions.predictions,
      })
    });
  }

  render() {
    return (
      <>
        <ImagesControlButtons
          handleMultipleImages={this.handleMultipleImages}
          handleClearImages={this.handleClearImages}
          handleSendImages={this.handleSendImages}
          images={this.state.images}
          imagesIsChanged={this.state.imagesIsChanged}
          gender={this.state.gender}
        />
        <Toombler handleGenderToombler={this.handleGenderToombler}/>
        <ImagesGallery
          images={this.state.images}
          showRates={this.state.showRates}
          rates={this.state.rates}
        />
      </>
    );
  }
}


function Toombler({handleGenderToombler}) {
  return (
    <div
      className="container-fluid py-3"
      id="toombler"
    >
      <div
        className="d-inline-flex justify-content-center"
        onChange={(e) => handleGenderToombler(e)}
      >
        <div className="form-check px-4">
          <input
            className="form-check-input"
            type="radio"
            name="flexRadioDefault"
            id="mCheckBox"
          />
          <label
            className="form-check-label"
            htmlFor="mCheckBox"
          >
            <h5>М</h5>
          </label>
        </div>
        <div className="form-check px-4">
          <input
            className="form-check-input"
            type="radio"
            name="flexRadioDefault"
            id="wCheckBox"
          />
          <label
            className="form-check-label"
            htmlFor="wCheckBox"
          >
            <h5>Ж</h5>
          </label>
        </div>
      </div>
    </div>
  );
}


class Header extends React.Component {
  render() {
    return (
      <nav className="navbar bg-secondary" id="header">
        <div className="container-fluid">
          <svg
            width="32"
            height="32"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 512 512"
          >
            <path fill="#f8f9fa" d="M0 256a256 256 0 1 1 512 0A256 256 0 1 1 0 256zm407.4 75.5c5-11.8-7-22.5-19.3-18.7c-39.7 12.2-84.5 19-131.8 19s-92.1-6.8-131.8-19c-12.3-3.8-24.3 6.9-19.3 18.7c25 59.1 83.2 100.5 151.1 100.5s126.2-41.4 151.1-100.5zM160 120c-3.1 0-5.9 1.8-7.2 4.6l-16.6 34.7-38.1 5c-3.1 .4-5.6 2.5-6.6 5.5s-.1 6.2 2.1 8.3l27.9 26.5-7 37.8c-.6 3 .7 6.1 3.2 7.9s5.8 2 8.5 .6L160 232.5l33.8 18.3c2.7 1.5 6 1.3 8.5-.6s3.7-4.9 3.2-7.9l-7-37.8L226.4 178c2.2-2.1 3.1-5.3 2.1-8.3s-3.5-5.1-6.6-5.5l-38.1-5-16.6-34.7c-1.3-2.8-4.1-4.6-7.2-4.6zm192 0c-3.1 0-5.9 1.8-7.2 4.6l-16.6 34.7-38.1 5c-3.1 .4-5.6 2.5-6.6 5.5s-.1 6.2 2.1 8.3l27.9 26.5-7 37.8c-.6 3 .7 6.1 3.2 7.9s5.8 2 8.5 .6L352 232.5l33.8 18.3c2.7 1.5 6 1.3 8.5-.6s3.7-4.9 3.2-7.9l-7-37.8L418.4 178c2.2-2.1 3.1-5.3 2.1-8.3s-3.5-5.1-6.6-5.5l-38.1-5-16.6-34.7c-1.3-2.8-4.1-4.6-7.2-4.6z"/>
          </svg>
          <div id="telegram" className="d-flex justify-content-between">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="32"
              height="32"
              fill="currentColor"
              className="bi bi-telegram"
              viewBox="0 0 16 16"
            >
              <path fill="#f8f9fa" d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM8.287 5.906c-.778.324-2.334.994-4.666 2.01-.378.15-.577.298-.595.442-.03.243.275.339.69.47l.175.055c.408.133.958.288 1.243.294.26.006.549-.1.868-.32 2.179-1.471 3.304-2.214 3.374-2.23.05-.012.12-.026.166.016.047.041.042.12.037.141-.03.129-1.227 1.241-1.846 1.817-.193.18-.33.307-.358.336a8.154 8.154 0 0 1-.188.186c-.38.366-.664.64.015 1.088.327.216.589.393.85.571.284.194.568.387.936.629.093.06.183.125.27.187.331.236.63.448.997.414.214-.02.435-.22.547-.82.265-1.417.786-4.486.906-5.751a1.426 1.426 0 0 0-.013-.315.337.337 0 0 0-.114-.217.526.526 0 0 0-.31-.093c-.3.005-.763.166-2.984 1.09z"/>
            </svg>
            <a className="h5" href="https://t.me/yrasiq">@yrasiq</a>
          </div>
        </div>
      </nav>
    );
  }
}


class Description extends React.Component {
  render() {
    return (
      <div className="d-flex p-3 justify-content-center" id="description">
        <div className="card d-inline-flex">
          <div className="card-body">
            <ul>
              <li>Сервис для оценки того, насколько хорошо вы выглядите на фото</li>
              <li>На основе нейронных сетей</li>
              <li>Одновременно можно оценить до 4х фотографий</li>
              <li>На фото должно быть видно лицо</li>
              <li>На фото должен быть один человек</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }
}


class App extends React.Component {
    render() {
        return (
          <>
            <Header />
            <Description />
            <div className="container-fluid h-100">
              <PreviewMultipleImages />
              <div className="container" id="bottom"></div>
            </div>
          </>
        );
    };
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
