const words = [
"Secure Digital Banking",
"Transfer Money Instantly",
"Pay Bills Easily",
"Manage Your Accounts"
]

let i=0
let j=0
let current=""
let deleting=false

function type(){

current=words[i]

if(!deleting){
j++
}
else{
j--
}

document.getElementById("typing").innerHTML=current.substring(0,j)

if(j==current.length){
deleting=true
setTimeout(type,1000)
return
}

if(j==0){
deleting=false
i=(i+1)%words.length
}

setTimeout(type,100)
}

type()