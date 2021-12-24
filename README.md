# Voronoi Diagram
> 資工碩一 涂家浩 M103040005

![](demo.gif)

## 軟體規格書、軟體說明
### 輸出與輸入（資料）規格、功能規格與介面規格：
1. 讀取 測資.txt的方式為透過 terminal 執行並給予第一個參數為測資txt的檔名
2. 按下鍵盤 M 來算出 Voronoi
3. 按下 Enter 可觀看每個步驟
4. 按下 H 可畫出下一條 HP (Hyperplane)
5. 按下 N 可以觀看合成步驟動畫，再次按N可加速
6. 測資讀取完畢後畫面會停留在最後一個 Voronoi Diagram，這時可以用滑鼠隨意新增點
7. 使用滑鼠新增點可透過「點選」以及「拖曳揮灑」兩種方式
8. 按下 Backspace 可刪掉剛剛新增的點
9. 按下 0 可刪掉所有點
10. 按下 Ctrl + S 可儲存執行結果
11. 讀取過去儲存的 執行結果.txt 方式同讀取測資
12. 不加參數打開此程式可直接用滑鼠新增點
### 軟體測試規劃書 (可改善之處)
經過開發確認會出現精度問題，兩條應該要相交的線可能因為精度問題而算出他們「差點相交」這個差距值目前透過一個固定的 threshold 來容忍它。在演算法邏輯中，在某些狀況理論上是必定會產生交點的。那萬一程式真的沒有找到交點，目前沒有深究到底要如何處理，也許是找到差距最小的那一個焦點吧。

## 程式設計
資料結構是依照老師提供的文件實作
### 需注意的細節或特別的技巧
#### Convex Hull
1. 洽在 convex hull 上的點都必須納入
2. 當所有點共線，雙向的線上都要包含所有的點。E.g. 有 A,B,C,D 四點共線且照順序排，則 convex hull 組成為 A-B-C-D-C-B-A。
#### 如何找出交點
- 可參考 https://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect 
#### HP (Hyperplane)
1. HP 一定是由上而下走 (PPT第四章 第 34 頁：_The HP is monotonic in y_)，而用來建造 HP 的每個左右配對點也都一定會往下走，如果新的左右配對點沒有往下走，則不可採納
2. 既然 HP 一定是由上而下走，那麼一個點是在 HP 左邊還是右邊就可以輕易被算出，一條被 HP 砍斷的線哪一頭是在右邊也可被算出
3. 算完整條 HP 再去把「在 HP 右邊的原本屬於左邊的線、及反之」刪掉，因為這些線在計算 HP 的過程中還不能確定他們不會跟 HP 相交
#### Step-by-Step
- 開兩個 thread，然後用 Condition 及 Mutex 去暫停一個 recursive function
## 軟體測試與實驗結果
- 語言：Python 3.9.5
- 編譯器：PyInstaller
- 系統：Windows 10
- 所需記憶體大小：約 30 MB

測試極限：可成功畫出 1072 點，約末 2000 點時就有較大機會產生錯誤

## 心得
這份作業包含很多小細節，需要仔細思考才能找出問題點與解決辦法。將每個步驟畫出來並且印出相關資訊才能比較好 debug。實際上回頭看會發現重要觀念其實老師的PPT第四章有寫，只不過可能是因為寫得非常簡短，所以容易被忽略。

像是 PPT 第四章 第 34 頁：_The HP is monotonic in y_ 這句話的意思其實是「HP 一定是由上而下走」 (反過來說成由下往上走也是一樣)，只是可能沒看懂。

## 附錄
- [程式原始碼 (合併檔)](voronoi.py)
- 測試輸入檔
    - [主要測資 utf8 含自己的測資](test_data\vd_testdata.in%20utf8.txt)
    - [主要測資 big5  含自己的測資](test_data\vd_testdata.in%20big5.txt)
    - [主要測資 無註解 含自己的測資](test_data\vd_testdata_pure.in.txt)
    - [1072點](test_data\1072.txt)
- 測試輸出檔
    - [1072 result](saved_results\1072%20result.txt)
