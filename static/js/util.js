var div = document.getElementById('parking-lot');
//car 1
// div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 25px; top: 0px;' />";
// //car 2
// div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 25px; top: 100px;' />";
// //car 3
// div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 25px; top: 200px;' />";
// //car 4
// div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 500px; top: 0px;' />";
// //car 5
// div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 500px; top: 100px;' />";
// //car 6
// div.innerHTML += "<img src='/static/img/car.png' width='160' height='120' style='position: absolute; left: 500px; top: 200px;' />";



drawPoint([98,50]);
drawPoint([98,150]);
drawPoint([98,250]);
drawPoint([578,50]);
drawPoint([578,150]);
drawPoint([578,250]);

drawPoint([438,50]);
drawPoint([438,150]);
drawPoint([438,250]);

drawPoint([438,390]);

var pathes=[[[438,390],[438,50],[98,50]],
            [[438,390],[438,150],[98,150]],
            [[438,390],[438,250],[98,250]],
            [[438,390],[438,50],[578,50]],
            [[438,390],[438,150],[578,150]],
            [[438,390],[438,250],[578,250]]];

drawLines(pathes[0]);
drawLines(pathes[1]);
drawLines(pathes[2]);
drawLines(pathes[3]);
drawLines(pathes[4]);
drawLines(pathes[5]);

function drawLines(points) {
  var c = document.getElementById("myCanvas");
  var ctx = c.getContext("2d");
  var gradient = ctx.createLinearGradient(0, 0, 500, 0);
  gradient.addColorStop("0", "magenta");
  gradient.addColorStop("0.5" ,"blue");
  gradient.addColorStop("1.0", "red");

  ctx.strokeStyle = gradient;
  ctx.lineWidth = 3;


  for (var i = 0; i < points.length-1; i++) {
    ctx.beginPath();
    ctx.moveTo(points[i][0],points[i][1]);
    ctx.lineTo(points[i+1][0],points[i+1][1]);
    ctx.stroke();
  }
}



function drawPoint(point){
  var c= document.getElementById("myCanvas");
  var ctx=c.getContext("2d");
  ctx.fillRect(point[0],point[1],2,2);
}