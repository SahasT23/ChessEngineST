import copy
# This class is responsible for storing all information about the current state of a chess game.
# It will also be used to check for valid moves and potential moves
# Will also contain a move log

class GameState():
    def __init__(self):
        # Board is an 8x8 2D list and each element in the list has 2 characters
        # First letter is the colour and second is the piece name
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        self.moveFunctions = {'p': self.getPawnMoves, 'R': self.getRookMoves, 'N': self.getKnightMoves,
                              'B': self.getBishopMoves, 'Q': self.getQueenMoves, 'K': self.getKingMoves}

        self.whiteToMove = True
        self.moveLog = []
        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.checkmate = False
        self.stalemate = False
        self.enpassantPossible = ()  # Co-ordinates for the square where an en-passant capture is possible
        self.enpassantPossibleLog = [self.enpassantPossible]
        self.currentCastlingRight = CastleRights(True, True, True, True)
        self.castleRightsLog = [CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                             self.currentCastlingRight.wqs, self.currentCastlingRight.bqs)]



        #self.protects = [][]
        #self.threatens = [][]
        #self.squaresCanMoveTo = [][]


    def makeMove(self, move):
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move) # So we can undo the move later
        self.whiteToMove = not self.whiteToMove # Swaps the players
        # Update the King's location if moved
        if move.pieceMoved == 'wK':
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 'bK':
            self.blackKingLocation = (move.endRow, move.endCol)

        # Pawn promotion
        if move.isPawnPromotion:
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + 'Q'

        # En-passant move
        if move.isEnpassantMove:
            self.board[move.startRow][move.endCol] = '--' # Capturing the pawn

        # Update the enpassantPossible Variable
        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:  # Only for two square pawn advances
            self.enpassantPossible = ((move.startRow + move.endRow)//2, move.endCol)
        else:   # Any time a move is made with the engine, sets en-passant possible, then resets if it isn't a pawn
            self.enpassantPossible = ()

        # Castle move
        if move.isCastleMove:
            if move.endCol - move.startCol == 2:
                self.board[move.endRow][move.endCol-1] = self.board[move.endRow][move.endCol+1]
                self.board[move.endRow][move.endCol+1] = '--' # Erases the old Rook
            else:
                self.board[move.endRow][move.endCol+1] = self.board[move.endRow][move.endCol-2]
                self.board[move.endRow][move.endCol-2] = '--'

        self.enpassantPossibleLog.append(self.enpassantPossible)

        # Update the castling rights whenever it is a Rook or a King move
        self.updateCastleRights(move)
        self.castleRightsLog.append(CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                            self.currentCastlingRight.wqs, self.currentCastlingRight.bqs))



    def undoMove(self):
        if len(self.moveLog) != 0:
            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove
            # Update the King's location
            if move.pieceMoved == 'wK':
                self.whiteKingLocation = (move.startRow, move.startCol)
            elif move.pieceMoved == 'bK':
                self.blackKingLocation = (move.startRow, move.startCol)
            # Undo the en-passant move
            if move.isEnpassantMove:
                self.board[move.endRow][move.endCol] = '--'  # Leave the 'landing' square empty
                self.board[move.startRow][move.endCol] = move.pieceCaptured

            self.enpassantPossibleLog.pop()
            self.enpassantPossible = self.enpassantPossibleLog[-1]

            # Undo castling rights
            self.castleRightsLog.pop() # Gets rid of the new castle rights from the move that we are undoing
            castleRights = copy.deepcopy(self.castleRightsLog[-1])
            self.currentCastlingRight = castleRights
            # Undo castle move
            if move.isCastleMove:
                if move.endCol - move.startCol == 2: # King side castle
                    self.board[move.endRow][move.endCol+1] = self.board[move.endRow][move.endCol-1]
                    self.board[move.endRow][move.endCol-1] = '--'
                else: # Queen side castle
                    self.board[move.endRow][move.endCol-2] = self.board[move.endRow][move.endCol+1]
                    self.board[move.endRow][move.endCol+1] = '--'


            self.checkmate = False;
            self.stalemate = False;

    def updateCastleRights(self, move):
        if move.pieceMoved == 'wK':
            self.currentCastlingRight.wks = False
            self.currentCastlingRight.wqs = False
        elif move.pieceMoved == 'bK':
            self.currentCastlingRight.bks = False
            self.currentCastlingRight.bqs = False
        elif move.pieceMoved == 'wR':
            if move.startRow == 7:
                if move.startCol == 0:  # Left Rook
                    self.currentCastlingRight.wqs = False
                elif move.startCol == 7: # Right Rook
                    self.currentCastlingRight.wks = False
        elif move.pieceMoved == 'bR':
            if move.startRow == 0:
                if move.startCol == 0:  # Left Rook
                    self.currentCastlingRight.bqs = False
                elif move.startCol == 7: # Right Rook
                    self.currentCastlingRight.bks = False

        #if a rook is captured
        if move.pieceCaptured == 'wR':
            if move.endRow == 7:
                if move.endCol == 0:
                    self.currentCastlingRight.wqs = False
                elif move.endCol == 7:
                    self.currentCastlingRight.wks = False
        elif move.pieceCaptured == 'bR':
            if move.endRow == 0:
                if move.endCol == 0:
                    self.currentCastlingRight.bqs = False
                elif move.endCol == 7:
                    self.currentCastlingRight.bks = False


    def getValidMoves(self):
        tempEnpassantPossible = self.enpassantPossible
        tempCastleRights = CastleRights(self.currentCastlingRight.wks, self.currentCastlingRight.bks,
                                        self.currentCastlingRight.wqs, self.currentCastlingRight.bqs) # Copies the current castling rights
        # 1. Get all possible moves
        moves = self.getAllPossibleMoves()
        if self.whiteToMove:
            self.getCastleMoves(self.whiteKingLocation[0], self.whiteKingLocation[1], moves)
        else:
            self.getCastleMoves(self.blackKingLocation[0], self.blackKingLocation[1], moves)
        # 2. Make the move for each move
        for i in range(len(moves)-1, -1, -1):  # Going backwards through the list
            self.makeMove(moves[i])
            # 3. Generate all opponent's moves
            # 4. For each of the opponent's moves, see if the enemy piece attacks your king
            self.whiteToMove = not self.whiteToMove
            if self.inCheck():
                moves.remove(moves[i])
            self.whiteToMove = not self.whiteToMove
            self.undoMove() # 5. If they do attack the king, there it will not be a valid move
        if len(moves) == 0:
            if self.inCheck():
                self.checkmate = True
            else:
                self.stalemate = True

        self.enpassantPossible = tempEnpassantPossible
        self.currentCastlingRight = tempCastleRights
        return moves


    def inCheck(self):  # Determines if the current player is in check
        if self.whiteToMove:
            return self.squareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.squareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])


    def squareUnderAttack(self, r, c):  # Determines if the enemy can attack the square (r,c)
        self.whiteToMove = not self.whiteToMove  # Switches to the opponent's turn
        oppMoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove
        for move in oppMoves:
            if move.endRow == r and move.endCol == c:
                return True
        return False



    def getAllPossibleMoves(self):
        moves = []
        for r in range(len(self.board)): # Row count
            for c in range(len(self.board[r])): # Column count per given row
                turn = self.board[r][c][0]
                if (turn == 'w' and self.whiteToMove) or (turn == 'b' and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r, c, moves)  # Calls upon the appropriate move function for the piece type
        return moves


    def getPawnMoves(self, r, c, moves):
        if self.whiteToMove:  # White pawn will move
            if self.board[r-1][c] == "--":  # One square pawn advance
                moves.append(Move((r, c), (r-1, c), self.board))
                if r == 6 and self.board[r-2][c] == "--":   # Two square pawn advance
                    moves.append(Move((r, c), (r-2, c), self.board))
            if c-1 >= 0:  # Captures to the left of the pawn
                if self.board[r-1][c-1][0] == 'b':   # Enemy piece to be captured
                    moves.append(Move((r, c), (r-1, c-1), self.board))
                elif (r-1, c-1) == self.enpassantPossible:
                    moves.append(Move((r, c), (r-1, c-1), self.board, isEnpassantMove=True))
            if c+1 <= 7:  # Captures to the right of the pawn
                if self.board[r-1][c+1][0] == 'b':   # Enemy piece to be captured
                    moves.append(Move((r, c), (r-1, c+1), self.board))
                elif (r-1, c+1) == self.enpassantPossible:
                    moves.append(Move((r, c), (r-1, c+1), self.board, isEnpassantMove=True))

        else:  # Black pawn will move
            if self.board[r+1][c] == "--":  # One square pawn advance
                moves.append(Move((r, c), (r+1, c), self.board))
                if r == 1 and self.board[r+2][c] == "--":   # Two square pawn advance
                    moves.append(Move((r, c), (r+2, c), self.board))
            if c-1 >= 0:  # Captures to the left of the pawn
                if self.board[r+1][c-1][0] == 'w':
                    moves.append(Move((r, c), (r+1, c-1), self.board))
                elif (r+1, c-1) == self.enpassantPossible:
                    moves.append(Move((r, c), (r+1, c-1), self.board, isEnpassantMove=True))
            if c+1 <= 7:  # Captures to the right of the pawn
                if self.board[r+1][c+1][0] == 'w':   # Enemy piece to be captured
                    moves.append(Move((r, c), (r+1, c+1), self.board))
                elif (r+1, c+1) == self.enpassantPossible:
                    moves.append(Move((r, c), (r+1, c+1), self.board, isEnpassantMove=True))
            # Add in pawn promotion

    def getRookMoves(self, r, c, moves):  # Gets rook moves for rook located at (row, col) and adds to move list
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1)) # Four diagonals
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8): # Bishop has a maximum square count of 7 squares
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:  # On the board
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--": # Empty space is valid
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    elif endPiece[0] == enemyColor: # enemy piece valid
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                        break
                    else: # Friendly piece invalid
                        break
                else:
                    break


    def getKnightMoves(self, r, c, moves):  # Gets knight moves for rook located at (row, col) and adds to move list
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        allyColor = "w" if self.whiteToMove else "b"
        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor: # Not an ally piece
                    moves.append(Move((r, c), (endRow, endCol), self.board))



    def getBishopMoves(self, r, c, moves):  # Gets bishop moves for rook located at (row, col) and adds to move list
        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--":
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    elif endPiece[0] == enemyColor:
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                        break
                    else:
                        break
                else: # Off the board
                    break


    def getQueenMoves(self, r, c, moves):   # Gets queen moves for rook located at (row, col) and adds to move list
        self.getRookMoves(r, c, moves)
        self.getBishopMoves(r, c, moves)


    def getKingMoves(self, r, c, moves):    # Gets king moves for rook located at (row, col) and adds to move list
        kingMoves = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
        allyColor = "w" if self.whiteToMove else "b"
        for i in range(8):
            endRow = r + kingMoves[i][0]
            endCol = c + kingMoves[i][1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor:
                    moves.append(Move((r, c), (endRow, endCol), self.board))


    def getCastleMoves(self, r, c, moves):
        if self.squareUnderAttack(r, c):
            return
        if (self.whiteToMove and self.currentCastlingRight.wks) or (not self.whiteToMove and self.currentCastlingRight.bks):
            self.getKingsideCastleMoves(r, c, moves)
        if (self.whiteToMove and self.currentCastlingRight.wqs) or (not self.whiteToMove and self.currentCastlingRight.bqs):
            self.getQueensideCastleMoves(r, c, moves)

    def getKingsideCastleMoves(self, r, c, moves):
        if self.board[r][c+1] == '--' and self.board[r][c+2] == '--':
            if not self.squareUnderAttack(r, c+1) and not self.squareUnderAttack(r, c+2):
                moves.append(Move((r, c), (r, c+2), self.board, isCastleMove=True))

    def getQueensideCastleMoves(self, r, c, moves):
        if self.board[r][c-1] == '--' and self.board[r][c-2] == '--' and self.board[r][c-3] == '--':
            if not self.squareUnderAttack(r, c-1) and not self.squareUnderAttack(r, c-2):
                moves.append(Move((r, c), (r, c-2), self.board, isCastleMove=True))


class CastleRights():
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move():
    # Maps the keys to the values
    # Key : value
    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4,
                   "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
                   "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board, isEnpassantMove=False, isCastleMove=False):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.isPawnPromotion = (self.pieceMoved == 'wp' and self.endRow == 0) or (self.pieceMoved == 'bp' and self.endRow == 7)
        # En-passant moves
        self.isEnpassantMove = isEnpassantMove
        if self.isEnpassantMove:
            self.pieceCaptured = 'wp' if self.pieceMoved == 'bp' else 'bp'

        self.isCapture = self.pieceCaptured != '--'
        # Castle Move
        self.isCastleMove = isCastleMove
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol



    def __eq__(self, other):
        if isinstance(other, Move):       # Overriding the equals method
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]

    def __str__(self): # Overriding the string method
        # Castle Move
        if self.isCastleMove:
            return "0-0" if self.endCol == 6 else "0-0-0"  # looking from White's position
                # 0-0 = Kingside Castle
                # 0-0-0 = Queenside Castle

        endSquare = self.getRankFile(self.endRow, self.endCol)

        # Pawn moves
        if self.pieceMoved[1] == 'p':
            if self.isCapture:
                return self.colsToFiles[self.startCol + 'x']
            else:
                return endSquare
            # Pawn Promotions

        # Two of the same type of piece moving to a square

        # also adding + for a check move and # for a checkmate

        # Piece moves
        moveString = self.pieceMoved[1]
        if self.isCapture:
            moveString += 'x'
        return moveString + endSquare
