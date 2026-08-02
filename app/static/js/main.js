const menu=document.getElementById("menuToggle");

const sidebar=document.getElementById("sidebar");

if(menu){

menu.onclick=function(){

sidebar.classList.toggle("show");

};

}