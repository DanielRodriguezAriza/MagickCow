# region XNA Math Class

# NOTE : This class' implementation looks to me like it's pretty inefficient and could be improved by a lot by using a single linear buffer rather than a list of lists, but whatever... we'll deal with this shit for now.
# NOTE : Matrices in XNA are always 4x4
class XNA_Matrix:
    # NOTE : The constructor returns the identity matrix by default
    def __init__(self, M11 = 1, M12 = 0, M13 = 0, M14 = 0, M21 = 0, M22 = 1, M23 = 0, M24 = 0, M31 = 0, M32 = 0, M33 = 1, M34 = 0, M41 = 0, M42 = 0, M43 = 0, M44 = 1):
        self.matrix = [[0 for j in range(0, 4)] for i in range(0, 4)]
        
        self.matrix[0][0] = M11
        self.matrix[0][1] = M12
        self.matrix[0][2] = M13
        self.matrix[0][3] = M14

        self.matrix[1][0] = M21
        self.matrix[1][1] = M22
        self.matrix[1][2] = M23
        self.matrix[1][3] = M24

        self.matrix[2][0] = M31
        self.matrix[2][1] = M32
        self.matrix[2][2] = M33
        self.matrix[2][3] = M34

        self.matrix[3][0] = M41
        self.matrix[3][1] = M42
        self.matrix[3][2] = M43
        self.matrix[3][3] = M44
    
    # TODO : Maybe add some "consturctor" static methods that return matrices constructed from specific input types? stuff like XNA_Matrix.FromBlenderMatrix(mat), XNA_Matrix.FromWhatever(...), etc...

# endregion
