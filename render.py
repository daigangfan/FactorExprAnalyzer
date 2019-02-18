
from parseexpr import pipeline
from jinja2 import FileSystemLoader,Environment
if __name__=="__main__":
    sentences=pipeline("((rank(decaylinear(delta((close),2),8))-rank(decaylinear(corr(((vwap*0.3)+(open*0.7)),sum(mean(volume,180),37),14),12)))*-1)")
    env=Environment(loader=FileSystemLoader(searchpath="./"))
    template=env.get_template("test_template.txt")
    result=template.render(sentences=sentences)
    print(result)