const menu=document.getElementById("menuToggle");

const sidebar=document.getElementById("sidebar");

if(menu){

menu.onclick=function(){

sidebar.classList.toggle("show");

};

}
document.addEventListener("click",function(e){

    if(window.innerWidth>991)return;

    if(!sidebar.contains(e.target)
        && !menu.contains(e.target)){

        sidebar.classList.remove("show");

    }

});